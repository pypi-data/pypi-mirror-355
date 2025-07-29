def plot_distribution(# plt.hist:
                      column, bins=30, color="skyblue", title=None,
                      alpha=0.7, edgecolor="black", linewidth=1.0,
                      density=False, histtype="bar", label=None, rwidth=None,

                      # plt.figure
                      fig_width = 8, fig_height = 5, outer_facecolor = 'lightgray',
                      dpi = 100, fig_edgecolor="darkgray", fig_linewidth = 10, frameon = True,
                      tight_layout = None, constrained_layout = None, layout = None,

                      # ax.set_facecolor
                      inner_facecolor = 'white',

                      # plt.title
                      title_fontsize = '14', title_color = 'black', title_loc = 'center', title_pad = 10,
                      title_fontweight = 'light', title_fontname = None, title_style = 'normal',

                      # plt.tick_params
                      tick_params = 'black',

                      # plt.x_label
                      xlabel_fontsize=10, xlabel_color='black', xlabel_labelpad=10,
                      xlabel_loc='center', xlabel_weight='light', xlabel_rotation=0,
                      xlabel_style='normal', xlabel_fontname=None,

                      # plt.y_label
                      y_fontsize = 10, ylabel_color = 'black',  ylabel_labelpad=10,
                      ylabel_loc='center', ylabel_weight='light', ylabel_rotation=90,
                      ylabel_style='normal', ylabel_fontname=None,

                      # plt.grid
                      grid_boolvalue = True, grid_linestyle="--", grid_alpha=0.75, grid_which = 'major',
                      grid_axis = 'both', grid_color = 'gray', grid_linewidth = 0.8, grid_zorder = None,

                      # plt.legend
                      legend_loc='upper right', legend_fontsize = 10, legend_title = 'Legend',
                      legendtitle_fontsize = 10, legend_frameon = True,legend_facecolor = 'lightgray',
                      legend_edgecolor = 'black', legend_ncol = 1, legend_labelspacing = 0.1,
                      legend_handlelength = 1.35, legend_shadow = True, legend_borderpad = None,
                      legend_fancybox = False, legend_columnspacing = None
):

    if title is None:
        title = f"Distribution of {column.name}"

    fig = plt.figure(figsize=(fig_width, fig_height), facecolor=outer_facecolor, dpi = dpi,
                     edgecolor = fig_edgecolor, linewidth = fig_linewidth, frameon = frameon,
                      tight_layout = tight_layout, constrained_layout = constrained_layout, layout = layout)  # light gray figure bg
    ax = plt.gca()
    ax.set_facecolor(inner_facecolor)  # slightly lighter plot area bg

    # Dynamically build kwargs
    kwargs = {
        "bins": bins,
        "color": color,
        "alpha": alpha,
        "edgecolor": edgecolor,
        "linewidth": linewidth,
        "density": density,
        "histtype": histtype
    }
    if label is not None:
        kwargs["label"] = label
    if rwidth is not None:
        kwargs["rwidth"] = rwidth

    # Plot
    plt.hist(column, **kwargs)

    plt.title(title, fontsize = title_fontsize, color = title_color, loc = title_loc, pad = title_pad,
                      fontweight = title_fontweight, fontname = title_fontname, style = title_style)

    plt.tick_params(colors=tick_params)

    plt.xlabel(column.name, fontsize = xlabel_fontsize, color = xlabel_color, labelpad = xlabel_labelpad,
               weight=xlabel_weight, rotation=xlabel_rotation, style=xlabel_style, fontname=xlabel_fontname)

    plt.ylabel("Density" if density else "Frequency", fontsize = y_fontsize, color = ylabel_color,
               labelpad = ylabel_labelpad, weight= ylabel_weight, rotation=ylabel_rotation, style=ylabel_style,
               fontname=ylabel_fontname)

    if label is not None:
        plt.legend(loc=legend_loc, fontsize = legend_fontsize, title = legend_title, title_fontsize = legendtitle_fontsize,
                   frameon = legend_frameon, facecolor = legend_facecolor, edgecolor = legend_edgecolor, ncol = legend_ncol,
                   labelspacing = legend_labelspacing, handlelength = legend_handlelength, shadow = legend_shadow,
                  borderpad = legend_borderpad, fancybox = legend_fancybox, columnspacing = legend_columnspacing)

    plt.grid(grid_boolvalue, linestyle= grid_linestyle, alpha=grid_alpha, which = grid_which, axis = grid_axis,
             color = grid_color, linewidth = grid_linewidth, zorder = grid_zorder)

    plt.tight_layout()

    plt.show()
