import pytest
from unittest.mock import MagicMock
from src.database.models.articles import Articles
from src.services.embedding_sync import _get_common_sentiment
import pytest
import numpy as np

def test_categorize_articles_success(mocker):
    mock_config = {"batch_size": 2}

    mock_session = mocker.MagicMock()
    mocker.patch("src.services.categorize_articles.get_session", return_value=mocker.MagicMock(__enter__=lambda s: mock_session))

    mock_article = mocker.MagicMock()
    mock_article.title = "Economic news"
    mock_article.summary = "Something about economic"
    mock_article.categories = None

    mock_session.scalars.return_value.all.side_effect = [[mock_article], []]

    mock_engine = mocker.patch("src.services.categorize_articles.ZeroShotEngine")
    mock_engine.return_value.predict.return_value = [["Economic", "Crypto"]]
    mock_engine.return_value.batch_size = 2

    from src.services.categorize_articles import categorize_articles
    categorize_articles(mock_config)

    assert mock_article.categories == ["Economic", "Crypto"]
    mock_session.commit.assert_called_once()
    mock_engine.return_value.predict.assert_called_with(["Economic news. Something about economic"])

def test_process_article_success(mocker):
    mock_session = mocker.MagicMock()
    mock_engine = mocker.MagicMock()

    article = Articles(id=1, title="Ukraine updates", summary="Economy growth", is_llm_processed=False)

    mock_entity = mocker.MagicMock()
    mock_entity.country_name = "Ukraine"
    mock_entity.sentiment = 0.8

    mock_result = mocker.MagicMock()
    mock_result.entities = [mock_entity]
    mock_engine.extract_news.return_value = mock_result

    mock_db_entity = mocker.MagicMock()
    mock_db_entity.name = "Ukraine"
    mock_db_entity.id = 101
    mock_session.scalars.return_value.all.return_value = [mock_db_entity]

    from src.services.country_sentiment_extraction import _process_article 
    success = _process_article(mock_session, article, mock_engine)

    assert success is True
    assert article.is_llm_processed is True
    assert mock_session.execute.called

    mock_engine.extract_news.assert_called_once_with("Ukraine updates. Economy growth")

def test_extraction_loop_termination(mocker):
    mock_session = mocker.MagicMock()
    mocker.patch("src.services.country_sentiment_extraction.get_session", return_value=mocker.MagicMock(__enter__=lambda s: mock_session))

    mock_session.scalars.return_value.all.return_value = []
    
    from src.services.country_sentiment_extraction import country_sentiment_extraction
    country_sentiment_extraction({"llm_batch_size": 10}, mocker.MagicMock())

    assert mock_session.scalars.called
    assert not mock_session.commit.called

@pytest.mark.parametrize("sentiments, expected", [
    ([], "unknown"),
    ([0.1, -0.1, 0.2], "Neutral"),
    ([-0.5, 0.1], "Negative"),
    ([0.5, -0.1], "Positive"),
    ([-0.5, 0.5], "Neutral"),
    ([-0.6, 0.3, 0.2], "Negative"),
])
def test_get_common_sentiment(sentiments, expected):
    assert _get_common_sentiment(sentiments) == expected

def test_process_unembedded_articles_logic(mocker):
    mock_session = mocker.MagicMock()
    mocker.patch("src.services.embedding_sync.get_session", return_value=mocker.MagicMock(__enter__=lambda s: mock_session))

    mock_engine = mocker.patch("src.services.embedding_sync.EmbeddingEngine")
    mock_engine.return_value.batch_size = 2

    mock_engine.return_value.predict.return_value = [np.array([0.1, 0.2]), np.array([0.9, 0.8])]

    article_with_analysis = mocker.MagicMock(id=1, analysis=mocker.MagicMock(), entities=[])
    article_without_analysis = mocker.MagicMock(id=2, analysis=None, entities=[])

    mock_session.scalars.return_value.all.side_effect = [[article_with_analysis, article_without_analysis], []]

    from src.services.embedding_sync import process_unembedded_articles
    process_unembedded_articles({"some": "config"})

    assert article_with_analysis.analysis.embedding == [0.1, 0.2]
    assert article_with_analysis.is_embedding_processed is True

    added_objects = [args[0] for args, kwargs in mock_session.add.call_args_list]
    assert any(obj.article_id == 2 for obj in added_objects)

    mock_session.commit.assert_called_once()