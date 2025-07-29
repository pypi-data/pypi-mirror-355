import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
from sqlalchemy.orm import Session
from crm_umkm.db.session import SessionLocal
from mcp.server.fastmcp import FastMCP 
from crm_umkm.server import (
    add_pelanggan, edit_pelanggan, list_pelanggan,
    catat_interaksi, kirim_promosi, ekspor_interaksi,
    tambah_produk, list_produk, update_stok_produk, cari_produk,
    riwayat_interaksi_pelanggan, rekomendasi_followup,
    hapus_pelanggan, hapus_produk, produk_terlaris,
    produk_favorit_pelanggan, pelanggan_terbaik,
    notifikasi_stok_menipis, catat_order_baru, ubah_status_order,
    export_laporan_aktivitas_mingguan, export_data_pelanggan,
    export_data_produk
)
from crm_umkm.db.models import OrderMasuk
from crm_umkm.db.init import init_db

from crm_umkm.db.schema import (
    AddPelangganArgs, EditPelangganArgs,
    ListPelangganArgs, CatatInteraksiArgs, KirimPromosiArgs,
    EksporInteraksiArgs, TambahProdukArgs, ListProdukArgs,
    UpdateStokProdukArgs, CariProdukArgs, RiwayatInteraksiPelangganArgs,
    HapusPelangganArgs, HapusProdukArgs, CatatOrderArgs,
    UpdateStatusOrderArgs, ExportAktivitasArgs, ExportDataArgs,
    JumlahDataArgs
)

TEST_DB = "crm_umkm.db"


class CRMUMKMTestCase(unittest.TestCase):
    def setUp(self):
        os.environ["DB_PATH"] = TEST_DB
        init_db()

    def get_session(self):
        return SessionLocal()
    
    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_add_and_list_pelanggan(self):
        add_pelanggan(AddPelangganArgs(nama="John Doe", no_hp="08123456789"))
        result = list_pelanggan(ListPelangganArgs())
        self.assertIn("John Doe", result)

    def test_edit_pelanggan(self):
        add_pelanggan(AddPelangganArgs(nama="Jane", no_hp="0811111111"))
        result = edit_pelanggan(EditPelangganArgs(nama="Jane", no_hp_baru="0822222222"))
        self.assertIn("berhasil diperbarui", result)

    def test_catat_interaksi(self):
        add_pelanggan(AddPelangganArgs(nama="IntTest", no_hp="0800000000"))
        result = catat_interaksi(CatatInteraksiArgs(pelanggan="IntTest", jenis="telepon"))
        self.assertIn("dicatat", result)

    @patch("requests.post")
    def test_kirim_promosi(self, mock_post):
        mock_post.return_value.status_code = 200
        add_pelanggan(AddPelangganArgs(nama="PromoUser", no_hp="0811223344"))
        result = kirim_promosi(KirimPromosiArgs(pelanggan="PromoUser", isi_pesan="Promo!"))
        self.assertIn("terkirim", result)

    def test_tambah_dan_cari_produk(self):
        tambah_produk(TambahProdukArgs(nama="ProdukA", kategori="Makanan", harga=10000, stok=10))
        result = cari_produk(CariProdukArgs(keyword="ProdukA"))
        self.assertIn("ProdukA", result)

    def test_update_stok_produk(self):
        tambah_produk(TambahProdukArgs(nama="ProdukStok", harga=2000, stok=5))
        result = update_stok_produk(UpdateStokProdukArgs(nama="ProdukStok", stok_baru=20))
        self.assertIn("diperbarui", result)

    def test_hapus_pelanggan(self):
        add_pelanggan(AddPelangganArgs(nama="DelUser", no_hp="0877777777"))
        result = hapus_pelanggan(HapusPelangganArgs(nama="DelUser"))
        self.assertIn("dihapus", result)

    def test_hapus_produk(self):
        tambah_produk(TambahProdukArgs(nama="DelProduk", harga=3000, stok=7))
        result = hapus_produk(HapusProdukArgs(nama="DelProduk"))
        self.assertIn("dihapus", result)

    def test_catat_order_dan_ubah_status(self):
        add_pelanggan(AddPelangganArgs(nama="OrderUser", no_hp="0898989898"))
        tambah_produk(TambahProdukArgs(nama="OrderProduk", harga=5000, stok=15))
        catat_order_baru(CatatOrderArgs(pelanggan="OrderUser", produk="OrderProduk", jumlah=2))

        # Now get the order ID using a fresh session, consistent with what ubah_status_order expects
        with self.get_session() as db:
            order = db.query(OrderMasuk).filter_by(pelanggan="OrderUser").first()
            order_id = order.id

        # Call ubah_status_order separately
        result = ubah_status_order(UpdateStatusOrderArgs(order_id=order_id, status_baru="sold"))
        self.assertIn("diperbarui", result)

if __name__ == '__main__':
    unittest.main()