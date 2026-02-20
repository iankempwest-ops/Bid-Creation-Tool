import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kw-bid-tool-dev-key-change-in-prod')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_DIR, 'bid_tool.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    PDF_FOLDER = os.path.join(DATA_DIR, 'pdfs')
    TEMPLATE_DIR = os.path.join(DATA_DIR, 'templates')
    BID_TEMPLATE_PATH = os.path.join(DATA_DIR, 'templates', 'Master Bid Template.xlsx')
    WA_TAX_API = 'https://webgis.dor.wa.gov/webapi/AddressRates.aspx'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
