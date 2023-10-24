import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from argparse import ArgumentParser
from cycler import cycler
from pathlib import Path

from lrc_file.LrcFile import LrcFile, Run
from .PlotConfig import PlotConfig


def main() -> None:
    argparser = create_parser()
    args = argparser.parse_args()

    mpl.style.use("classic")

    plot_cfg = PlotConfig(
        lnst_data_file_path=args.data_file,
        view=args.view,
        runs=args.run,
        flows=args.flow,
        ylim=args.ylim,
        legend=not args.no_legend,
        aggregated_flows=args.aggregated_flows,
    )
    fig = plot_data(plot_cfg)

    if args.save or args.output:
        if args.output:
            output_filepath = args.output
        else:
            data_file_path = Path(args.data_file)
            output_filepath = f"{data_file_path.stem}.{args.view}.png"

        fig.savefig(output_filepath)
        print(f"Saved to file {output_filepath}")
    else:
        fig.tight_layout()
        plt.show()

def create_parser() -> ArgumentParser:
    argparser = ArgumentParser(
        description="The tool visualizes the CPU or iperf throughput samples "
                    "from each perf_test iteration of the ENRT recipes"
    )

    argparser.add_argument(
        dest="data_file", type=str, help="an exported LNST recipe run data file"
    )
    argparser.add_argument(
        "--view",
        type=str,
        choices=["cpu", "flow"],
        required=True,
        help="display either CPU or flow samples",
    )
    argparser.add_argument(
        "--run",
        type=int,
        action="append",
        help="display only the specified run",
    )
    argparser.add_argument(
        "--flow",
        type=int,
        action="append",
        help="display only the specified flow",
    )
    argparser.add_argument(
        "--aggregated-flows",
        action="store_true",
        help="display aggregated flows instead of all individual flows"
    )
    argparser.add_argument(
        "--ylim",
        type=float,
        help="limit the y-scale of all graphs to the specified value, otherwise the axes will be automatically limited",
    )
    save_group = argparser.add_mutually_exclusive_group()
    save_group.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="saves the generated figure into a file instead of displaying it, "
             "the filename is derived from the source data filename with the suffix "
             "replaced, to override the filename completely, use -o argument",
    )
    save_group.add_argument(
        "-o",
        "--output",
        type=str,
        help="saves the generated figure into the specified file instead of "
             "displaying it",
    )
    argparser.add_argument(
        "--debug", action="store_true", help="print some debugging information"
    )
    argparser.add_argument(
        "--no-legend", action="store_true", help="do not display legend"
    )
    return argparser


def plot_data(plot_cfg: PlotConfig):
    fig = plt.figure(figsize=(25, 15))
    colors = ["black", "blue", "orange", "green", "red", "purple", "brown", "pink", "gray", "olive", "cyan", "lime", "tan"]
    plt.rc("axes", prop_cycle=cycler(color=colors))

    data_type = plot_cfg.view
    data_file = LrcFile(plot_cfg.lnst_data_file_path)

    runs: list[Run]
    if data_type == "cpu":
        runs = data_file.get_raw_cpu_data()
    elif data_type == "flow":
        runs = data_file.get_raw_flow_data(
            aggregated_flows_only=plot_cfg.aggregated_flows,
            flow_whitelist=plot_cfg.flows
        )
    else:
        raise Exception(f"Data type {data_type} not supported.")

    try:
        # calculate maximum values of generator and receiver
        generator_runs_max: float = max(
            sample
            for run in runs
            for series in run.generator_series
            for sample in series.data
        )
        receiver_runs_max: float = max(
            sample
            for run in runs
            for series in run.receiver_series
            for sample in series.data
        )
    except ValueError:
        raise Exception("--flow list matched no flows")

    all_axes: list[Axes] = []
    number_of_runs: int = len(plot_cfg.runs) if plot_cfg.runs is not None else len(runs)
    plotted_runs = 0
    for run_index, run in enumerate(runs):
        if plot_cfg.runs is not None and run_index not in plot_cfg.runs:
            print(f"skipping run {run_index}")
            continue

        # create generator and receiver subplots
        for col_number, (run_series, runs_maximum) in enumerate([
            (run.generator_series, generator_runs_max),
            (run.receiver_series, receiver_runs_max),
        ], 1):
            # create subplot
            ax: Axes = fig.add_subplot(number_of_runs, 2, 2 * plotted_runs + col_number)
            all_axes.append(ax)

            # plot series
            plotted_lines: list[Line2D] = []
            for series in run_series:
                y = ax.plot(series.data, label=series.label)[0]
                plotted_lines.append(y)

            # show legend
            if plot_cfg.legend:
                ax.legend(
                    handles=plotted_lines,
                    fontsize="x-small",
                    framealpha=0.8,
                    loc=1,
                    ncol=4,
                )

            # set axes grid and limits
            ax.grid(axis="y", color="darkgray", linestyle=":", linewidth=2)
            ax.set_xlim(
                left=-3,
                right=max(len(series.data) for series in run_series) + 3
            )
            ax.set_ylim(
                top=runs_maximum * 1.10 if plot_cfg.ylim is None else plot_cfg.ylim,
                bottom=-5.0,
                auto=True
            )
        plotted_runs += 1

    # set yaxis formatter for flow data
    if data_type == "flow" and data_file.recipe_name != "ShortLivedConnectionsRecipe":
        for ax in all_axes:
            fmtr = ticker.FuncFormatter(lambda x, _: f"{x * 1e-9:.2f}")
            ax.yaxis.set_major_formatter(fmtr)

    return fig
