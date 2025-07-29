from tempsave import init, save

init(clean=True)

a = 10  # noqa: F841
o = save(a)


def fn():
    return 10


b = save(fn)()

del a, b

try:
    print(f"{a=} {b=}")
    assert False
except Exception as e:
    pass

init()
print(f"Post-reload: {a=} {b=}")
