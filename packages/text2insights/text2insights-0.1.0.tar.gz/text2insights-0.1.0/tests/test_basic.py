from text2insights import analyze_text

def test_analyze_text():
    result = analyze_text("SARB raised rates due to inflation")
    assert 'sentiment' in result
    assert 'keywords' in result
    assert 'entities' in result