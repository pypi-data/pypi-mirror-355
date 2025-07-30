from mm_strk import domain


async def test_address_to_domain_exist():
    res = await domain.address_to_domain("0x0060b56b67e1b4dd1909376496b0e867f165f31c5eac7902d9ff48112f16ef9b")
    assert res.is_ok()
    assert res.unwrap() == "abc.stark"


async def test_address_to_domain_async_not_exist():
    res = await domain.address_to_domain("0x0060b56b67e1b4dd1909376496b0e867f165f31c5eac7902d9ff48112f16ef9a")  # not existed
    assert res.is_ok()
    assert res.unwrap() is None
