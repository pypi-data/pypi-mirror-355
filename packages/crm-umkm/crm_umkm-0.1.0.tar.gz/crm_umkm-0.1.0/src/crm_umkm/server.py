from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
import os
import csv
import requests
from crm_umkm.db.schema import (
    AddPelangganArgs,EditPelangganArgs,ListPelangganArgs,
    CatatInteraksiArgs,KirimPromosiArgs,EksporInteraksiArgs,
    TambahProdukArgs,ListProdukArgs,UpdateStokProdukArgs,
    CariProdukArgs,RiwayatInteraksiPelangganArgs,HapusPelangganArgs,HapusProdukArgs,
    CatatOrderArgs,UpdateStatusOrderArgs,
    ExportAktivitasArgs,ExportDataArgs,JumlahDataArgs
)
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, func, select, desc
from crm_umkm.db.models import Pelanggan, Produk, OrderMasuk, Penjualan, Interaksi
from crm_umkm.db.session import SessionLocal
from crm_umkm.db.init import init_db

init_db()

def get_session():
    return SessionLocal()

WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "https://api.whatsapp.com/send")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")  

mcp = FastMCP(
    name="UMKM CRM",
    description="CRM sederhana untuk UMKM dengan fitur pencatatan pelanggan, interaksi, produk, dan promosi",
    dependencies=["sqlalchemy", "requests", "pydantic"],
    instructions=(
        "Gunakan alat ini untuk mencatat pelanggan, produk, interaksi mereka, serta mengirim promosi via WhatsApp."
    )
)

@mcp.tool(annotations={"title": "Tambah Pelanggan", "description": "Tambahkan data pelanggan baru."})
def add_pelanggan(args: AddPelangganArgs) -> str:
    session = get_session()
    try:
        pelanggan = Pelanggan(
            nama=args.nama,
            no_hp=args.no_hp,
            alamat=args.alamat,
            tanggal_bergabung=args.tanggal_bergabung,
            kategori=args.kategori
        )
        session.add(pelanggan)
        session.commit()
        return f"✅ Pelanggan '{args.nama}' berhasil ditambahkan."
    except Exception as e:
        session.rollback()
        return f"❌ Gagal menambahkan pelanggan: {e}"
    finally:
        session.close()

@mcp.tool(annotations={"title": "Edit Data Pelanggan", "description": "Edit nomor HP, alamat, atau kategori pelanggan."})
def edit_pelanggan(args: EditPelangganArgs) -> str:
    session = get_session()
    try:
        pelanggan = session.query(Pelanggan).filter_by(nama=args.nama).first()
        if not pelanggan:
            return f"❌ Pelanggan '{args.nama}' tidak ditemukan."

        if args.no_hp_baru:
            pelanggan.no_hp = args.no_hp_baru
        if args.alamat_baru:
            pelanggan.alamat = args.alamat_baru
        if args.kategori_baru:
            pelanggan.kategori = args.kategori_baru

        session.commit()
        return f"✏️ Data pelanggan '{args.nama}' berhasil diperbarui."
    finally:
        session.close()


@mcp.tool(annotations={"title": "Hapus Pelanggan", "description": "Hapus pelanggan dari database berdasarkan nama."})
def hapus_pelanggan(args: HapusPelangganArgs) -> str:
    session = get_session()
    try:
        pelanggan = session.query(Pelanggan).filter_by(nama=args.nama).first()
        if not pelanggan:
            return f"❌ Pelanggan '{args.nama}' tidak ditemukan."

        session.delete(pelanggan)
        session.commit()
        return f"✏️ Data pelanggan '{args.nama}' berhasil dihapus."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Daftar Pelanggan", "description": "Lihat semua pelanggan berdasarkan kategori (opsional)."})
def list_pelanggan(args: ListPelangganArgs) -> str:
    session = get_session()
    try:
        query = session.query(Pelanggan)
        if args.kategori:
            query = query.filter_by(kategori=args.kategori)
        rows = query.all()

        if not rows:
            return "⚠️ Tidak ada pelanggan ditemukan."

        return "\n".join(["--- Daftar Pelanggan ---"] + [f"{r.nama} | {r.no_hp} | {r.kategori}" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Catat Interaksi", "description": "Catat interaksi pelanggan."})
def catat_interaksi(args: CatatInteraksiArgs) -> str:
    session = get_session()
    try:
        interaksi = Interaksi(
            pelanggan=args.pelanggan,
            tanggal=datetime.now().strftime("%Y-%m-%d"),
            jenis=args.jenis,
            catatan=args.catatan
        )
        session.add(interaksi)
        session.commit()
        return f"📒 Interaksi dengan '{args.pelanggan}' dicatat."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Kirim Promosi WhatsApp", "description": "Kirim pesan promosi ke pelanggan via WhatsApp."})
def kirim_promosi(args: KirimPromosiArgs) -> str:
    db = get_session()
    try:
        pelanggan = db.query(Pelanggan).filter_by(nama=args.pelanggan).first()
        if not pelanggan:
            return f"❌ Pelanggan '{args.pelanggan}' tidak ditemukan."

        nomor = pelanggan.no_hp
        headers = {"Authorization": f"Bearer {WHATSAPP_API_TOKEN}"}
        payload = {"to": nomor, "message": args.isi_pesan}
        try:
            r = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
            if r.status_code == 200:
                return f"✅ Pesan terkirim ke {args.pelanggan}."
            else:
                return f"❌ Gagal mengirim pesan: {r.text}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    finally:
        db.close()

@mcp.tool(annotations={"title": "Ekspor Interaksi", "description": "Ekspor semua data interaksi ke file CSV."})
def ekspor_interaksi(args: EksporInteraksiArgs) -> str:
    db = get_session()
    try:
        rows = db.query(Interaksi).all()
        if not rows:
            return "⚠️ Tidak ada data interaksi."

        with open(args.filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "pelanggan", "tanggal", "jenis", "catatan"])
            writer.writerows([[r.id, r.pelanggan, r.tanggal, r.jenis, r.catatan] for r in rows])

        return f"✅ Data interaksi diekspor ke '{args.filename}'."
    finally:
        db.close()

@mcp.tool(annotations={"title": "Tambah Produk", "description": "Tambahkan produk ke database."})
def tambah_produk(args: TambahProdukArgs) -> str:
    session = get_session()
    try:
        produk = Produk(
            nama=args.nama,
            kategori=args.kategori,
            harga=args.harga,
            stok=args.stok
        )
        session.add(produk)
        session.commit()
        return f"📦 Produk '{args.nama}' berhasil ditambahkan."
    finally:
        session.close()
    

@mcp.tool(annotations={"title": "Daftar Produk", "description": "Lihat daftar produk, bisa difilter berdasarkan kategori."})
def list_produk(args: ListProdukArgs) -> str:
    session = get_session()
    try:
        if args.kategori:
            rows = session.query(Produk).filter_by(kategori=args.kategori).all()
        else:
            rows = session.query(Produk).all()
        if not rows:
            return "⚠️ Tidak ada produk ditemukan."

        return "\n".join(["--- Daftar Produk ---"] + [f"{r.nama} | {r.kategori} | Rp{r.harga:,} | Stok: {r.stok}" for r in rows])
    finally:
        session.close()    


@mcp.tool(annotations={"title": "Hapus Produk", "description": "Hapus produk dari database berdasarkan nama."})
def hapus_produk(args: HapusProdukArgs) -> str:
    session = get_session()
    try:
        produk = session.query(Produk).filter_by(nama=args.nama).first()
        if not produk:
            return f"❌ Produk '{args.nama}' tidak ditemukan."
        session.delete(produk)
        session.commit()
        return f"🗑️ Produk '{args.nama}' telah dihapus."
    finally:
        session.close()


@mcp.tool(annotations={"title": "Daftar Produk Terlaris", "description": "Lihat daftar produk terlaris."})
def produk_terlaris(args: JumlahDataArgs) -> str:
    session = get_session()
    try:
        results = (
            session.query(Penjualan.produk, func.sum(Penjualan.jumlah).label("total"))
            .group_by(Penjualan.produk)
            .order_by(func.sum(Penjualan.jumlah).desc())
            .limit(args.total)
            .all()
        )

        if not results:
            return "📊 Belum ada data penjualan."

        return "\n".join(["🔥 Produk Terlaris:"] + [f"{r[0]} - {r[1]}x terjual" for r in results])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Update Stok Produk", "description": "Perbarui jumlah stok produk."})
def update_stok_produk(args: UpdateStokProdukArgs) -> str:
    session = get_session()
    try:
        produk = session.query(Produk).filter_by(nama=args.nama).first()
        if not produk:
            return f"❌ Produk '{args.nama}' tidak ditemukan."
        produk.stok = args.stok_baru
        session.commit()
        return f"🔄 Stok produk '{args.nama}' diperbarui ke {args.stok_baru}."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Cari Produk", "description": "Cari produk berdasarkan nama."})
def cari_produk(args: CariProdukArgs) -> str:
    session = get_session()
    try:
        rows = session.query(Produk).filter(Produk.nama.like(f"%{args.keyword}%")).all()

        if not rows:
            return f"🔍 Tidak ditemukan produk dengan kata kunci '{args.keyword}'."

        return "\n".join(["--- Hasil Pencarian Produk ---"] + [f"{r.nama} | {r.kategori} | Rp{r.harga:,} | Stok: {r.stok}" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Riwayat Interaksi Pelanggan", "description": "Lihat riwayat interaksi dengan pelanggan tertentu."})
def riwayat_interaksi_pelanggan(args: RiwayatInteraksiPelangganArgs) -> str:
    session = get_session()
    try:
        rows = session.query(Interaksi).filter_by(pelanggan=args.pelanggan).order_by(Interaksi.tanggal.desc()).all()

        if not rows:
            return f"📭 Tidak ada interaksi dengan '{args.pelanggan}'."

        return "\n".join([f"📅 {r.tanggal} | {r.jenis} | {r.catatan}" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Rekomendasi Follow-up", "description": "Rekomendasikan pelanggan yang perlu dihubungi ulang."})
def rekomendasi_followup() -> str:
    batas = datetime.now() - timedelta(days=30)
    session = get_session()
    try:
        subq = session.query(
            Interaksi.pelanggan,
            func.max(Interaksi.tanggal).label("terakhir")
        ).group_by(Interaksi.pelanggan).subquery()

        rows = session.query(Pelanggan.nama, subq.c.terakhir).outerjoin(
            subq, Pelanggan.nama == subq.c.pelanggan
        ).filter((subq.c.terakhir == None) | (subq.c.terakhir < batas)).all()

        if not rows:
            return "👍 Semua pelanggan sudah dihubungi dalam 30 hari terakhir."

        return "\n".join(["🔔 Perlu Follow-up:"] + [f"{r[0]} (terakhir: {r[1] or 'belum pernah'})" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Produk Favorit Pelanggan", "description": "Lihat daftar produk yang paling disukai oleh masing-masing pelanggan."})
def produk_favorit_pelanggan(args: JumlahDataArgs) -> str:
    session = get_session()
    try:
        pelanggan_list = session.query(Penjualan.pelanggan).distinct().all()
        if not pelanggan_list:
            return "📊 Tidak ada data pelanggan yang membeli."

        hasil = []
        for (pelanggan,) in pelanggan_list:
            rows = (
                session.query(Penjualan.produk, func.sum(Penjualan.jumlah))
                .filter(Penjualan.pelanggan == pelanggan)
                .group_by(Penjualan.produk)
                .order_by(desc(func.sum(Penjualan.jumlah)))
                .limit(args.total)
                .all()
            )
            if rows:
                hasil.append(f"👤 {pelanggan}:")
                hasil.extend([f" - {r[0]} ({r[1]}x)" for r in rows])
        return "\n\n".join(hasil) if hasil else "Tidak ada produk favorit."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Daftar Pelanggan Terbaik", "description": "Lihat daftar pelanggan yang paling setia."})
def pelanggan_terbaik(args: JumlahDataArgs) -> str:
    session = get_session()
    try:
        rows = (
            session.query(Penjualan.pelanggan, func.sum(Penjualan.jumlah).label("total"))
            .group_by(Penjualan.pelanggan)
            .order_by(desc("total"))
            .limit(args.total)
            .all()
        )
        if not rows:
            return "📊 Belum ada transaksi penjualan."
        return "\n".join(["👑 Pelanggan Paling Setia:"] + [f"{r[0]} - {r[1]} item" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Notifikasi Produk Menipis", "description": "Notifikasi jika ada produk yang sudah harus diisi ulang stoknya."})
def notifikasi_stok_menipis(threshold: int = 10) -> str:
    session = get_session()
    try:
        rows = session.query(Produk.nama, Produk.stok).filter(Produk.stok <= threshold).order_by(Produk.stok.asc()).all()
        if not rows:
            return "✅ Tidak ada produk dengan stok menipis."
        return "\n".join(["🚨 Notifikasi Stok Rendah:"] + [f"{r[0]} - stok tinggal {r[1]}" for r in rows])
    finally:
        session.close()

@mcp.tool(annotations={"title": "Catat Order Baru", "description": "Mencatat jika ada order baru."})
def catat_order_baru(args: CatatOrderArgs) -> str:
    session = get_session()
    try:
        order = OrderMasuk(
            pelanggan=args.pelanggan,
            produk=args.produk,
            jumlah=args.jumlah,
            tanggal=args.tanggal,
            status="pending"
        )
        session.add(order)
        session.commit()
        return "📥 Order baru dicatat sebagai pending."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Ubah Status Order", "description": "Mengubah status order."})
def ubah_status_order(args: UpdateStatusOrderArgs) -> str:
    session = get_session()
    try:
        order = session.query(OrderMasuk).filter_by(id=args.order_id).first()
        if not order:
            return "❌ Order tidak ditemukan."

        if args.status_baru.lower() == "sold":
            penjualan = Penjualan(
                pelanggan=order.pelanggan,
                produk=order.produk,
                jumlah=order.jumlah,
                tanggal=datetime.now().strftime("%Y-%m-%d")
            )
            session.add(penjualan)

            produk = session.query(Produk).filter_by(nama=order.produk).first()
            if produk:
                produk.stok -= order.jumlah

        order.status = args.status_baru
        session.commit()

        return f"📦 Status order #{args.order_id} diperbarui menjadi {args.status_baru}."
    finally:
        session.close()

@mcp.tool(annotations={"title": "Laporan Mingguan", "description": "Lihat laporan aktivitas mingguan."})
def export_laporan_aktivitas_mingguan(args: ExportAktivitasArgs) -> str:
    akhir = datetime.now()
    awal = akhir - timedelta(days=7)
    session = get_session()
    try:
        with open(args.filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tanggal", "Pelanggan", "Produk", "Jumlah"])
            rows = session.query(Penjualan.tanggal, Penjualan.pelanggan, Penjualan.produk, Penjualan.jumlah).filter(
                Penjualan.tanggal.between(awal.strftime("%Y-%m-%d"), akhir.strftime("%Y-%m-%d"))
            ).all()
            writer.writerows(rows)
        return f"📄 Laporan aktivitas mingguan diekspor ke {args.filename}"
    finally:
        session.close()

@mcp.tool(annotations={"title": "Ekspor Data Pelanggan", "description": "Ekspor data pelanggan."})
def export_data_pelanggan(args: ExportDataArgs) -> str:
    filename = args.filename or f"data_pelanggan_{datetime.now().strftime('%Y%m%d')}.csv"
    session = get_session()
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nama", "No HP", "Alamat", "Tanggal Bergabung", "Kategori"])
            rows = session.query(Pelanggan).all()
            for r in rows:
                writer.writerow([r.id, r.nama, r.no_hp, r.alamat, r.tanggal_bergabung, r.kategori])
        return f"📄 Data pelanggan berhasil diekspor ke {filename}"
    finally:
        session.close()

@mcp.tool(annotations={"title": "Ekspor Data Produk", "description": "Ekspor data produk."})
def export_data_produk(args: ExportDataArgs) -> str:
    filename = args.filename or f"data_produk_{datetime.now().strftime('%Y%m%d')}.csv"
    session = get_session()
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nama", "Kategori", "Harga", "Stok"])
            rows = session.query(Produk).all()
            for r in rows:
                writer.writerow([r.id, r.nama, r.kategori, r.harga, r.stok])
        return f"📦 Data produk berhasil diekspor ke {filename}"
    finally:
        session.close()

def main():
    mcp.run()

if __name__ == "__main__":
    main()