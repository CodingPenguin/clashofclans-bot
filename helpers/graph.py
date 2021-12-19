import discord
from matplotlib import pyplot as plt

def plot_trophy_graph(data):
    dates = list(data.keys())
    trophy_values = list(map(int, list(data.values())))
    
    plt.figure(facecolor="#2F3136")
    plt.plot(dates, trophy_values, marker='o', color='white') 
    plt.tight_layout()
    plt.text(dates[-1], trophy_values[-1], f'{trophy_values[-1]}   ', horizontalalignment='right', color="white")
    
    ax = plt.gca()
    ax.set_facecolor(('#2F3136'))
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('#2F3136') 
    ax.spines['right'].set_color('#2F3136')
    ax.spines['left'].set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
        
    labels = [item.get_text() for item in ax.get_xticklabels()]
    new_labels = ['']*len(labels)
    new_labels[0], new_labels[len(new_labels)-1] = labels[0], labels[len(labels)-1]
    ax.set_xticklabels(new_labels)
    plt.savefig('graph.png')
    plt.clf()

def set_graph_embed(author_name):
    embed_var = discord.Embed(
        title=f"**{author_name}** Trophy Graph",
        description="All-time Graph",
        color=0x000000
    )
    embed_var.set_image(url="attachment://graph.png")
    return embed_var
# END COC GRAPH HELPERS