from mm_apt import ans


async def test_address_to_primary_name():
    address = "0x68e6982c788b50e3caccc834a4764763381d7201be996914e1310139a35854ed"
    assert (await ans.address_to_primary_name(address)).unwrap() == "vitalik"

    address = "0xabfabdec0732564bd906fb94e467410a131c6e6040f7bca860458e2026e3b14e"
    assert (await ans.address_to_primary_name(address)).unwrap() is None


async def test_address_to_name_async():
    address = "0x68e6982c788b50e3caccc834a4764763381d7201be996914e1310139a35854ed"
    assert (await ans.address_to_name(address)).unwrap() == "vitalik"

    address = "0xabfabdec0732564bd906fb94e467410a131c6e6040f7bca860458e2026e3b14e"
    assert (await ans.address_to_primary_name(address)).unwrap() is None
