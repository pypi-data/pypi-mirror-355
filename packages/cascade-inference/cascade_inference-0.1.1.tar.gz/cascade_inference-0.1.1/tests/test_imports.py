def test_import():
    try:
        import cascade
        import cascade.chat
        import cascade.chat.completions
    except ImportError as e:
        assert False, f"Failed to import cascade package: {e}" 