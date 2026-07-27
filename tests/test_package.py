def test_package_import() -> None:
    import forecast_ops

    assert forecast_ops.__doc__ == "ForecastOps package."