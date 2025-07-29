from sqlalchemy import Column, Integer, String, Text, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .session import Base
import os

class Pelanggan(Base):
    __tablename__ = 'pelanggan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String, nullable=False)
    no_hp = Column(String, nullable=False)
    alamat = Column(Text)
    tanggal_bergabung = Column(String)
    kategori = Column(String)

class Produk(Base):
    __tablename__ = 'produk'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String, nullable=False)
    kategori = Column(String)
    harga = Column(Integer)
    stok = Column(Integer)

class OrderMasuk(Base):
    __tablename__ = 'order_masuk'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pelanggan = Column(String, nullable=False)
    produk = Column(String, nullable=False)
    tanggal = Column(String)
    jumlah = Column(Integer)
    status = Column(String)

class Penjualan(Base):
    __tablename__ = 'penjualan'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pelanggan = Column(String, nullable=False)
    produk = Column(String, nullable=False)
    tanggal = Column(String)
    jumlah = Column(Integer)

class Interaksi(Base):
    __tablename__ = 'interaksi'
    id = Column(Integer, primary_key=True, autoincrement=True)
    pelanggan = Column(String, nullable=False)
    tanggal = Column(String)
    jenis = Column(String)
    catatan = Column(Text)
