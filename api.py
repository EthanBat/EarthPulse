import shutil

from fastapi import FastAPI, File, UploadFile
import uvicorn
import rasterio
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import earthpy.plot as ep


app = FastAPI()


@app.get("/")
async def hello_world():
    return {"hello": "world"}


@app.post("/attributes/")
async def attributes(file: UploadFile = File(...)):
    with open(f"{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    ds = rasterio.open(file.filename)

    # could not serialize crs and bounds
    data = {"filename": file.filename, "width": ds.width, "height": ds.height, "band_count": ds.count, "crs": print(ds.crs), "bounds": print(ds.bounds) }
    return data


@app.post("/thumbnail/")
async def thumbnail(file: UploadFile = File(...)):
    with open(f"{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    img = Image.open(file.filename)
    MAX_SIZE = (100, 100)
    img.thumbnail(MAX_SIZE)
    if "tif" in file.filename:
        outfile = file.filename[:-3] + "png"
    elif "tiff" in file.filename:
        outfile = file.filename[:-4] + "png"
    out = img.convert("RGB")
    out.save(outfile, "JPEG", quality=90)
    return { "file converted successfully" }


@app.post("/nvdi/")
async def nvdi(file: UploadFile = File(...)):
    with open(f"{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with rasterio.open(file.filename) as src:
        band_red = src.read(3)
    with rasterio.open(file.filename) as src:
        band_nir = src.read(4)

    # Allow division by zero
    np.seterr(divide='ignore', invalid='ignore')

    band_nir = np.array(band_nir)
    band_red = np.array(band_red)

    NDVI = (band_nir.astype(float) - band_red.astype(float)) / (band_nir + band_red)

    fig1, ax = plt.subplots(figsize=(12, 12))
    fig1 = plt.gcf()
    ep.plot_bands(NDVI,
                  cmap='PiYG',
                  scale=False,
                  cbar=True,  # Change this to FALSE to hide the color bar
                  ax=ax,
                  vmin=-1, vmax=1,
                  title="NDVI")
    fig1.savefig('NDVI.png', bbox_inches='tight')
    return { "nvdi has been calculated successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)