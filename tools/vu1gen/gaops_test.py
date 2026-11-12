"""Unit tests for Task GA ops added to lbmodel.py."""
import sys
import unittest

sys.path.insert(0, "tools/vu1gen")
import lbmodel


class TestGAOps(unittest.TestCase):
    def test_upper_decode(self):
        # OPMULA: op >= 0x3C, funct2 = 0x2E
        # dest=xyz (0xE), ft=2, fs=1, fd=0, op=0x3C, funct2=0x2E -> ((0x2E & 0x7C) << 4) | (0x2E & 3)
        funct2 = 0x2E
        e_hi = (funct2 & 0x7C) << 4
        e_lo = funct2 & 3
        # u = (dest << 21) | (ft << 16) | (fs << 11) | (fd << 6) | e_hi | 0x3C | e_lo
        # In upper_decode: op = u & 0x3F. If op >= 0x3C: e = (u & 3) | ((u >> 4) & 0x7C).
        u_opmula = (0xE << 21) | (2 << 16) | (1 << 11) | e_hi | 0x3C | e_lo
        dec = lbmodel.upper_decode(u_opmula)
        self.assertIsNotNone(dec)
        self.assertEqual(dec[0], "fmac")
        self.assertEqual(dec[1], 4)  # MUL
        self.assertEqual(dec[2], "cross")
        self.assertTrue(dec[4])  # toacc = True

        # OPMSUB: op = 0x2E
        u_opmsub = (0xE << 21) | (2 << 16) | (1 << 11) | (3 << 6) | 0x2E
        dec = lbmodel.upper_decode(u_opmsub)
        self.assertIsNotNone(dec)
        self.assertEqual(dec[0], "fmac")
        self.assertEqual(dec[1], 3)  # MSUB
        self.assertEqual(dec[2], "cross")
        self.assertFalse(dec[4])  # toacc = False

    def test_sqrt_helpers(self):
        # sqrt(4.0) = 2.0
        import struct
        four_bits = struct.unpack("<I", struct.pack("<f", 4.0))[0]
        two_bits = struct.unpack("<I", struct.pack("<f", 2.0))[0]
        self.assertEqual(lbmodel.sqrtq(four_bits), two_bits)
        self.assertEqual(lbmodel.sqrt_di(four_bits), 0)

        # rsqrt(1.0, 4.0) = 0.5
        one_bits = struct.unpack("<I", struct.pack("<f", 1.0))[0]
        half_bits = struct.unpack("<I", struct.pack("<f", 0.5))[0]
        val, di = lbmodel.rsqrtq(one_bits, four_bits)
        self.assertEqual(val, half_bits)
        self.assertEqual(di, 0)


if __name__ == "__main__":
    unittest.main()
