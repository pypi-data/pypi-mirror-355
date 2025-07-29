

# def get_layers_to_visualize(imgPath : Path):
#     # Load the full z stack, this will be handled later by napari
#     #img_fpath = Path("./data/flat-01.ome.tiff")
#     #img_fpath = Path("./data/193_S_CTRL_Before.ome.tiff")
#     img_name = imgPath.name
#     img_name = img_name.split(".ome.tiff")[0]

#     #img_fpath = Path("./data/curved-01.ome.tiff")
#     reader = OMETIFFReader(fpath=imgPath)
#     img_array, metadata, xml_metadata = reader.read()
#     nframes = img_array.shape[0]
#     # img_array.shape

#     channel_0 = img_array[0]  # shape: (140, 512, 512)
#     channel_1 = img_array[1]  # shape: (140, 512, 512)

#     channel_0.shape

#     surface_path = Path(f"./data/{img_name}_surface.ome.tiff")
#     reader = OMETIFFReader(fpath=surface_path)
#     surface, metadata, xml_metadata = reader.read()
#     surface.shape

#     blobs_path = Path(f"./data/{img_name}_blobs.ome.tiff")
#     reader = OMETIFFReader(fpath=blobs_path)
#     blobs, metadata, xml_metadata = reader.read()

#     df = pd.read_csv(f"./data/{img_name}_vector_table.csv")

#     # Reconstruct Napari vectors array
#     starts = df[['z0', 'y0', 'x0']].to_numpy()
#     ends   = df[['z1', 'y1', 'x1']].to_numpy()
#     ends = np.ones_like(starts)*30
#     shifts = df[['dz', 'dy', 'dx']].to_numpy()
#     vectors = np.stack([starts.astype(np.float32), shifts.astype(np.float32)], axis=1)  # shape: (n, 2, 3)

#     voxel_size = np.array([metadata['PhysicalSizeZ'], metadata['PhysicalSizeY'], metadata['PhysicalSizeX']])  # in microns
#     #scaling = voxel_size/voxel_size.max()
#     # for layer in viewer.layers:
#     #     layer.scale = voxel_size

#     return (channel_0, "image"), (surface, "surface"), (blobs, "blobs"), (vectors,"vectors"), voxel_size

#     # vectors.shape

#     # Start Napari viewer
#     # viewer = napari.Viewer()

#     # # Add the image to the viewer
#     # viewer.add_image(channel_0)
#     # viewer.add_labels(surface, name="surface")
#     # viewer.add_labels(blobs, name="blobs")
#     # viewer.add_vectors(vectors, name="vectors", edge_color='lime')

