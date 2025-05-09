import streamlit as st
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.image as mpimg
import io

# Set page wide
st.set_page_config(layout="wide")

st.title("🌎 Beautiful GeoTIFF Map Generator")
st.write("Upload your GeoTIFF, set legend labels/colors, upload compass rose, and generate a beautiful map!")

# Upload TIFF
uploaded_tif = st.file_uploader("Upload GeoTIFF file", type=["tif", "tiff"])

# Upload Compass Rose
uploaded_compass = st.file_uploader("Upload Compass Rose Image (PNG)", type=["png"])

# Define number of classes
n_classes = st.number_input("Number of classes (excluding NoData/Null)", min_value=1, max_value=20, value=5, step=1)

# Enter legend names and colors
legend_labels = {}
st.subheader("Define Class Labels and Colors")
for i in range(1, n_classes + 1):
    col1, col2 = st.columns(2)
    with col1:
        label = st.text_input(f"Class {i} Name:", value=f"Class {i}")
    with col2:
        color = st.color_picker(f"Class {i} Color:", value="#FFFFFF")
    legend_labels[i] = (label, color)

# Button to generate map
if st.button("Generate Map") and uploaded_tif is not None and uploaded_compass is not None:

    # Read TIFF
    with rasterio.open(uploaded_tif) as src:
        image = src.read(1)
        image = np.where(image == 0, np.nan, image)  # Mask NoData values
        left, bottom, right, top = src.bounds
        transform = src.transform
        pixel_size_x, pixel_size_y = transform[0], -transform[4]

    # Setup figure
    fig = plt.figure(figsize=(16, 11))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Set correct extent
    ax.set_extent([left, right, bottom, top], crs=ccrs.PlateCarree())

    # Prepare colormap
    cmap = mcolors.ListedColormap([legend_labels[i][1] for i in sorted(legend_labels.keys())])
    norm = mcolors.BoundaryNorm(sorted(legend_labels.keys()) + [max(legend_labels.keys())+1], cmap.N)

    # Show raster image
    show(image, transform=transform, ax=ax, cmap=cmap, norm=norm)

    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.7, color='gray', alpha=0.7, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}

    # Add Compass Rose Image
    compass_img = mpimg.imread(uploaded_compass)
    newax = fig.add_axes([0.88, 0.8, 0.08, 0.15], anchor='NE', zorder=10)
    newax.imshow(compass_img)
    newax.axis('off')

    # Add Scalebar
    scalebar = ScaleBar(dx=pixel_size_x, units='m', length_fraction=0.2,
                        location='lower left', scale_loc='bottom', box_alpha=0.5, color='black', border_pad=0.5)
    ax.add_artist(scalebar)

    # Create Legend
    legend_patches = [mpatches.Patch(color=color, label=label) for label, color in 
                      [legend_labels[i] for i in sorted(legend_labels.keys())]]
    leg = ax.legend(handles=legend_patches, loc='lower right', frameon=True, fontsize=10, title="Classes", title_fontsize=12)
    leg.get_frame().set_edgecolor('black')

    # Title
    plt.title("Generated Land Use Land Cover Map", fontsize=20, fontweight='bold', pad=20)

    # Tidy layout
    plt.tight_layout()

    # Show Plot
    st.pyplot(fig)

    # Save and offer download
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    st.download_button("📥 Download Map as PNG", buf.getvalue(), "generated_map.png", "image/png")

    buf_pdf = io.BytesIO()
    fig.savefig(buf_pdf, format="pdf", dpi=300)
    st.download_button("📥 Download Map as PDF", buf_pdf.getvalue(), "generated_map.pdf", "application/pdf")
