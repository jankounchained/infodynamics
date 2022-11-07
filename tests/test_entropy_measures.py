from infodynamics.measures.entropy import kld, jsd

def test_zero_change():
    zero_kld = kld(p=[1/2, 1/2], q=[1/2, 1/2])
    zero_jsd = jsd(p=[1/2, 1/2], q=[1/2, 1/2])
    assert zero_kld == 0 and zero_jsd == 0

def test_negative():
    pass