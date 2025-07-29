from rich.pretty import pprint as PP


def main():
    import trimesh
    import numpy as np
    import matplotlib.pyplot
    from trimesh.path.entities import Line, Arc, Bezier
    import matplotlib.image as mpimg
    import qrcode

    filename = "/Users/robertdegen/webseiten/comparts/src/BC215BCA-EF8F-4469-920E-FD67604CFC20/build.scad.stl"
    print(filename)
    mesh = trimesh.load(filename)
    print("done")
    plane_origin = [0,0,10]
    plane_normal = [0,0,1]
    
    section = mesh.section(plane_origin=plane_origin,plane_normal=plane_normal)

    if section is not None:
        slice_2d, to_3d = section.to_planar()
        width = 210
        height = 297
        width_inch = width / 25.4
        height_inch = height / 25.4

        fig, ax = matplotlib.pyplot.subplots(figsize=(width_inch, height_inch))

        ax = fig.add_axes([0, 0, 1, 1])

        min_xy, max_xy = slice_2d.bounds
        center_slice = (min_xy + max_xy) / 2
        center_page = np.array([width/2, height/2])
        shift = center_page - center_slice

        slice_2d.apply_translation(shift)

        discretized = slice_2d.discrete
        for segment in discretized:
            #PP(segment)
            xs, ys = segment[:, 0], segment[:, 1]
            ax.plot(xs,ys,color="black")

            #PP(entity)
            # if isinstance(entity, (Line, Arc, Bezier)):
            #     #PP(type(entity))
            #     try:
            #         if hasattr(entity.points, "__len__"):
            #             PP(entity.points)
            #         if hasattr(entity.points, "__len__") and len(entity.points) == 2:
            #             points = entity.discrete(50)
            #             xs, ys = points[:, 0], points[:, 1]
            #             ax.plot(xs,ys,color="black")
            #             print(".")
            #     except:
            #         print(type(entity))
            #         pass
        
        #ax.set_aspect("equal")
        #ax.autoscale_view()

    
        major_ticks = np.arange(0, max(width, height), 10)
        minor_ticks = np.arange(0, max(width, height), 1)

        ax.set_xticks(major_ticks)
        ax.set_yticks(major_ticks)
        ax.set_xticks(minor_ticks, minor=True)
        ax.set_yticks(minor_ticks, minor=True)

        grid_alpha = 0.3

        ax.grid(which='minor', color='lightgrey', linewidth=0.3, alpha=grid_alpha)
        ax.grid(which='major', color='grey', linewidth=0.7, alpha=grid_alpha)

        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.invert_yaxis()  # damit oben = 0 ist, wie auf Papier üblich
        ax.set_aspect('equal')
        ax.tick_params(labelbottom=False, labelleft=False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        #ax.axis('off')
        
        # ax.set_xticks(np.arange(0, 210, 1))
        # ax.set_yticks(np.arange(0, 297, 1))
        # ax.grid(which='minor', color='lightgrey', linewidth=0.5)

        # ax.set_xticks(np.arange(0, 210, 10), minor=False)
        # ax.set_yticks(np.arange(0, 297, 10), minor=False)
        # ax.grid(which='major', color='grey', linewidth=1)


        #ax.axis("off")
        
        #matplotlib.pyplot.show()
        #matplotlib.pyplot.savefig("test.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
        
        #ax.text(10, 10, "Schnitt auf Z=10mm öäüß\nhuhuhu", fontsize=12, color="black")
        ax.text(10, 20, "Schnitt auf Z=10mm öäüß\nhuhuhu", fontfamily='monospace', fontsize=9, color="black",bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.3"))
        ax.text(10, 30, "Schnitt auf Z=10mm öäüß\nhuhuhu", fontweight="bold", fontfamily='monospace', fontsize=9, color="black",bbox=dict(facecolor="white", edgecolor="none", boxstyle="round,pad=0.3"))

        alpha_x = 0.4;
        alpha_y = 1.0;

        for x_ in range(0, 21):
            ax.text(10*x_ + 0.8, 3, "%d" % (x_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_x)
            if x_ > 0 and x_ < 20:
                ax.text(10*x_ + 0.8, 297-5, "%d" % (x_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_x)
                ax.text(10*x_ + 0.8, 180+2, "%d" % (x_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_x)
                ax.text(10*x_ + 0.8, 80+2, "%d" % (x_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_x)

        for y_ in range(1, 30):
            ax.text(1, 10*y_ + 2, "%d" % (y_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_y, fontweight="bold")
            ax.text(210-4, 10*y_ + 2, "%d" % (y_*10), fontfamily='monospace', fontsize=5, color="black", alpha=alpha_y, fontweight="bold")

        #img = mpimg.imread("dein_bild.png")

        # Bild platzieren: extent = (x_min, x_max, y_min, y_max)
        #ax.imshow(img, extent=(x0, x1, y0, y1))


        qr = qrcode.make("Test Daten")
        qr_np = np.array(qr)
        x0, x1 = 10, 50
        y0, y1 = 250, 290  # Beachte deine invertierte Y-Achse!
        #y0, y1 = x0+qr_a, x1+qr_a  # Beachte deine invertierte Y-Achse!
        ax.imshow(qr_np, extent=(x0, x1, y0, y1), cmap='gray', zorder=100)


        matplotlib.pyplot.savefig("test.pdf", format="pdf", pad_inches=0)
        matplotlib.pyplot.close()
