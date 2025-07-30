import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker

# Data for the models
models = [
    ("Piper", 0.17, 0.09, "Ours"),
    ("StyleTTS2", 0.13, 0.50, "Ours"),
    # ("LoTHM", 0.10, 0.01, "Open"),
    ("HebTTS", 0.19, 25.44, "Open"),
    ("LoTHM", 0.10, 84.75, "Open"),
    ("MMS", 0.23, 0.21, "Open"),
    ("SASPEECH", 0.20, 0.16, "Open"),
    ("Robo-Shaul", 0.21, 1.58, "Open"),
    ("Google", 0.11, 4.08, "Proprietary"),
    ("OpenAI", 0.11, 1.60, "Proprietary"),
]

# Filter out models with None values for WER or RTF
filtered = [m for m in models if m[1] is not None and m[2] is not None]

# Create the figure and axes
fig, ax = plt.subplots(figsize=(10, 6))

# Plot each model
for name, wer, rtf, category in filtered:
    # Determine color based on category
    if name in ["Google", "OpenAI"]:
        color = '#f4c285'
    elif category == 'Ours':
        color = 'red'
    else:
        color = 'blue'

    # Determine size and weight for our models
    size = 200 if category == 'Ours' else 100
    weight = 'bold' if category == 'Ours' else 'normal'
    weight = 'normal' if name in ["Google", "OpenAI"] else weight

    # Create label for the point
    label = f"Ours ({name})" if category == 'Ours' else name

    # Plot the scatter point
    ax.scatter(rtf, wer, s=size, c=color, edgecolors='black', linewidths=1, zorder=3) # zorder to ensure points are above grid

    # Adjust text position for HebTTS to avoid overlap
    if name == "HebTTS":
        x_text = rtf * 0.85
        ha = 'right'
    elif name == "Google":
        x_text = rtf * 1.15  # right
        y_text = wer - 0.01  # slightly down
        ha = 'left'
    elif name == 'LoTHM':
        x_text = rtf * 0.90
    elif name == "OpenAI":
        x_text = rtf * 0.85  # left
        y_text = wer - 0.01  # slightly down
        ha = 'right'
    else:
        x_text = rtf * 1.15
        ha = 'left'

    # Add text label for each point
    ax.text(x_text, wer, label, fontsize=22, ha=ha, va='center', color='black', weight=weight, zorder=4)

# Set x-axis to log scale and format it
ax.set_xscale('log')
ax.tick_params(axis='both', which='major', labelsize=16)
ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
ax.xaxis.get_major_formatter().set_scientific(False)
ax.xaxis.get_major_formatter().set_useOffset(False)

# Set axis labels
ax.set_xlabel("RTF (lower is faster)", fontsize=22)
ax.set_ylabel("WER (lower is more accurate)", fontsize=22)

# Remove grid lines
ax.grid(False)

# Adjust layout to prevent labels from being cut off
plt.tight_layout()

# Extend x-axis limits by 20% to make space for labels/arrows
x_min, x_max = ax.get_xlim()
ax.set_xlim(x_min, x_max * 1.2)

# --- Add Arrows for Direction of Improvement ---

# Get current axis limits to position arrows relative to the plot
x_lims = ax.get_xlim()
y_lims = ax.get_ylim()

# Position arrow in upper-right area of plot, pointing to bottom-left
# Start point (upper-right area)
arrow_start_x = x_lims[1] * 0.002  # 80% across the x-axis
arrow_start_y = y_lims[1] * 0.55  # 85% up the y-axis

# End point (much closer to create shorter arrow with steeper angle)
arrow_end_x = x_lims[1] * 0.0006   # 60% across the x-axis (shorter horizontal distance)
arrow_end_y = y_lims[1] * 0.43   # 60% up the y-axis (steeper vertical drop)

# Draw arrow pointing from upper-right toward bottom-left
ax.annotate('',
            xy=(arrow_end_x, arrow_end_y),      # End point (arrow head)
            xytext=(arrow_start_x, arrow_start_y), # Start point (arrow tail)
            arrowprops=dict(facecolor='gray', shrink=0.05, width=0.5, headwidth=8, alpha=0.3),
            annotation_clip=False,
            zorder=1)  # Behind circles (3) and text (4)

# Clear any existing title and save the figure
plt.title("")
plt.savefig("plot.png", dpi=1200)
plt.show()