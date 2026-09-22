"""driver_guards.py - pre-eval asserts for eval drivers (P2 harness hardening).

Origin: the G3 footgun - a driver once emitted 295-byte argparse stubs
because --domains was missing, and block_size defaults to 128 while the
sonde-B protocol is 512. A 3-day ladder must not depend on eyeballing logs.

guards (all assert-style; they abort on violation):
  assert_block_size_512(cfg_dict)      block_size must be 512, not the 128 default
  assert_domains_present(argv)         --domains must be on the command line
  assert_output_size(path, minimum=300)  stub-shaped 295B output aborts
  assert_md5_pinned(path, expected)    checkpoint must match the pinned md5
  assert_routes_per_head(routes, n_head)  every route width divisible by n_head

--selftest: the stub-trap. Each trap must fire; if a guard fails to raise on
its bad input the selftest exits 1 (must FAIL when a guard does not work).
"""
import argparse
import hashlib
import sys

BLOCK_SIZE = 512
MIN_OUTPUT = 300


def assert_block_size_512(cfg_dict):
    bs = cfg_dict.get("block_size", 128)
    assert bs == BLOCK_SIZE, f"block_size={bs} but the sonde-B protocol requires {BLOCK_SIZE}"


def assert_domains_present(argv):
    assert any(str(a) == "--domains" for a in argv), \
        "driver called without --domains: the argparse stub is about to be emitted"


def assert_output_size(path, minimum=MIN_OUTPUT):
    import os
    n = os.path.getsize(path)
    assert n >= minimum, f"output {path} is {n}B, below the {minimum}B stub threshold"
    return n


def assert_md5_pinned(path, expected):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    got = h.hexdigest()
    assert got == expected, f"checkpoint md5 mismatch: got {got} expected {expected}"
    return got


def assert_routes_per_head(routes, n_head):
    bad = [r for r in routes if r % n_head]
    assert not bad, f"routes not whole per-head widths: {bad}"
    return True


def _selftest():
    ok = True

    def must_raise(label, fn):
        nonlocal ok
        try:
            fn()
            print(f"TRAP DID NOT FIRE: {label}")
            ok = False
        except AssertionError as e:
            print(f"trap fired: {label}: {e}")

    must_raise("block_size 128 default", lambda: assert_block_size_512({}))
    must_raise("missing --domains", lambda: assert_domains_present(["eval_router.py", "x.pt", "--routes", "8192"]))
    must_raise("stub output 295B", lambda: assert_output_size(_write_stub(295)))
    must_raise("routes not per-head", lambda: assert_routes_per_head([8192, 12287], 8))
    _good = _write_stub(400)
    must_raise("md5 mismatch", lambda: assert_md5_pinned(_good, "0" * 32))

    # guards must pass on good input
    assert_block_size_512({"block_size": 512})
    assert_domains_present(["prog", "--domains", "a:data.txt"])
    assert_output_size(_good)
    assert_routes_per_head([8192, 12288, 14336], 8)
    assert_md5_pinned(_good, _md5(_good))
    if ok:
        print("GUARDS_SELFTEST_OK all traps fired")
        return 0
    print("GUARDS_SELFTEST_FAILED")
    return 1


def _write_stub(nbytes):
    import os
    p = f"/tmp/guard_stub_{nbytes}.txt"
    if not os.path.exists(p):
        with open(p, "wb") as fh:
            fh.write(b"x" * nbytes)
    return p


def _md5(path):
    h = hashlib.md5()
    h.update(open(path, "rb").read())
    return h.hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    sys.exit(_selftest() if args.selftest else 0)
