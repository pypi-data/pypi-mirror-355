# tinygraphs.py
import matplotlib.pyplot as plt
from IPython.display import clear_output

def plot(train_losses, val_losses, epoch, theme='default', y_label = "Loss", x_label = "Epoch", title = "Epoch", updating_title = True, y_max = 0, legend = True, legend_loc = "upper right", dpi = 100, dark_mode = False):
    clear_output(wait=True)
    plt.figure(figsize=(5, 3))

    cmap = color_handling(theme)
    if dark_mode == True:
      plt.style.use('dark_background')



    plt.plot(train_losses, label='Train Loss', marker='o', color=cmap(0))
    plt.plot(val_losses,   label='Validation Loss', marker='x', color=cmap(1))

    plt.xlabel(x_label)
    plt.ylabel(y_label)

    plt.rcParams['figure.dpi'] = dpi

    if updating_title:
        plt.title(f"{title} {epoch+1}")
    else:
        plt.title(title)

    # Set y-axis limits
    if y_max > 0:
      plt.ylim(0, y_max)

    # Ensure x-axis has only whole-number ticks up to current epoch
    plt.xticks(range(len(train_losses)))

    if legend:
      plt.legend(loc=legend_handling(legend_loc))

    plt.show()

def legend_handling(legend_loc):
    locations = ['best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center']
    if legend_loc in locations:
        return legend_loc
    else:
        print(f"Warning: '{legend_loc}' not found. Supported arguments are: 'best', 'upper right', 'upper left', 'lower left', 'lower right', 'right', 'center left', 'center right', 'lower center', 'upper center', 'center'. Defaulting to 'upper right' instead.")
        return 'upper right'

def color_handling(theme):
    colormaps = {
        'viridis': 'viridis',     # Default - perceptually uniform, colorblind friendly
        'magma': 'magma',         # Good for black backgrounds
        'plasma': 'plasma',       # High contrast, good for continuous data
        'inferno': 'inferno',     # High contrast, good for printing in grayscale
        'cividis': 'cividis',     # Optimized for color vision deficiency
        'jet': 'jet',             # Classic rainbow (though not recommended for scientific vis)
        'coolwarm': 'coolwarm',   # Diverging - good for data centered around a midpoint
        'RdYlBu': 'RdYlBu',      # Red-Yellow-Blue - good for diverging data
        'YlOrRd': 'YlOrRd',      # Yellow-Orange-Red - good for sequential data
        'tab10': 'tab10'          # Qualitative - good for categorical data
    }
    if theme == 'default':
        return plt.colormaps.get_cmap('tab10')

    elif theme in colormaps:
        return plt.colormaps.get_cmap(colormaps[theme])

    else:
        # Default to viridis if an invalid scheme is provided
        print(f"Warning: '{theme}' not found. Using 'tab10' instead.")
        return plt.colormaps.get_cmap('tab10')