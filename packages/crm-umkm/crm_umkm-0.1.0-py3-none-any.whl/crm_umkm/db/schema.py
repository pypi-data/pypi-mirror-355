from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AddPelangganArgs(BaseModel):
    nama: str
    no_hp: str
    alamat: Optional[str] = ""
    tanggal_bergabung: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    kategori: Optional[str] = "Reguler"

class EditPelangganArgs(BaseModel):
    nama: str
    no_hp_baru: Optional[str] = None
    alamat_baru: Optional[str] = None
    kategori_baru: Optional[str] = None

class ListPelangganArgs(BaseModel):
    kategori: Optional[str] = ""

class CatatInteraksiArgs(BaseModel):
    pelanggan: str
    jenis: str
    catatan: Optional[str] = ""

class KirimPromosiArgs(BaseModel):
    pelanggan: str
    isi_pesan: str

class EksporInteraksiArgs(BaseModel):
    filename: str = "interaksi_export.csv"

class TambahProdukArgs(BaseModel):
    nama: str
    kategori: Optional[str] = ""
    harga: int
    stok: int

class ListProdukArgs(BaseModel):
    kategori: Optional[str] = ""

class UpdateStokProdukArgs(BaseModel):
    nama: str
    stok_baru: int

class CariProdukArgs(BaseModel):
    keyword: str

class RiwayatInteraksiPelangganArgs(BaseModel):
    pelanggan: str

class HapusPelangganArgs(BaseModel):
    nama: str

class HapusProdukArgs(BaseModel):
    nama: str

class CatatOrderArgs(BaseModel):
    pelanggan: str
    produk: str
    jumlah: int
    tanggal: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

class UpdateStatusOrderArgs(BaseModel):
    order_id: int
    status_baru: str

class ExportAktivitasArgs(BaseModel):
    filename: Optional[str] = Field(default_factory=lambda: f"laporan_aktivitas_{datetime.now().strftime('%Y%m%d')}.csv")

class ExportDataArgs(BaseModel):
    filename: Optional[str] = None

class JumlahDataArgs(BaseModel):
    total: int