import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator, FixedLocator
from matplotlib.patches import FancyArrowPatch

import pandas as pd
import scipy
import scipy.optimize


class Plotter:
    VERSION = "0.1.4"
    class Legend:
        def __init__(self, show = True):
            self.show = show
            self.position = "best"
        
        def Position(self, value):
            self.position = value
            return self

    class Graph:
        def __init__(self, x_values: list | np.ndarray | tuple | None = None, y_values: list | np.ndarray | tuple | None = None):
            if x_values is  None:
                self.x_values = []
            else:
                self.x_values = x_values
            if y_values is  None:
                self.y_values = []
            else:
                self.y_values = y_values
            self.x_range = None
            self.y_range = None

            self.x_mirror = False
            self.y_mirror = False
            self.xy_mirror = False
            self.z = None


        def X(self, x_values: list|np.ndarray|tuple):
            self.x_values = x_values
            return self
        def Y(self, y_values: list|np.ndarray|tuple):
            self.y_values = y_values
            return self
        def Z(self, value):
            self.z = value
            return self
        def xRange(self, min, max):
            self.x_range = (min, max)
            return self
        def yRange(self, min, max):
            self.y_range = (min, max)
            return self
        def Mirror(self, which="x"):
            if which == "x":
                self.x_mirror = True
            elif which == "y":
                self.y_mirror = True
            elif which == "xy":
                self.xy_mirror = True
            return self

    class Scatter:
        def __init__(self, x_values: list | np.ndarray | tuple | None = None, y_values: list | np.ndarray | tuple | None = None):
            if x_values is  None:
                self.x_values = []
            else:
                self.x_values = x_values
            if y_values is  None:
                self.y_values = []
            else:
                self.y_values = y_values
            self.x_range = None
            self.y_range = None

            self.x_range = None
            self.y_range = None

            self.x_mirror = False
            self.y_mirror = False
            self.xy_mirror = False
            self.z = None

        def Points(self, points: np.ndarray):
            if points.ndim != 2:
                print(f"Dimension is not 2 but {points.dim}")
                return self
            self.x_values = points[:, 0]
            self.y_values = points[:, 1]
            return self
        def Z(self, value):
            self.z = value
            return self
        def xRange(self, min, max):
            self.x_range = (min, max)
            return self
        def yRange(self, min, max):
            self.y_range = (min, max)
            return self
        def Mirror(self, which="x"):
            if which == "x":
                self.x_mirror = True
            elif which == "y":
                self.y_mirror = True
            elif which == "xy":
                self.xy_mirror = True
            return self

    class Line:
        """
        Defines Marker-Styling for used in Graph-Style Plots.\\
        Attributes are:\\
        Color()\\
        Width()\\
        Style()\\
        """
        def __init__(self):
            self.color = None
            self.width = 1
            self.style = "-"

        def Color(self, value):
            self.color = value
            return self
        def Width(self, value):
            self.width = value
            return self
        def Style(self, value):
            self.style = value
            return self
        
    class Marker:
        """
        Defines Marker-Styling for used in Graph- or Scatter-Style Plots.\\
        Attributes are:\\
        Color()\\
        Alpha()\\
        Size()\\
        Style()\\
        Step()
        """
        def __init__(self):
            self.color = None
            self.size = 1
            self.style = "o"
            self.step = None
            self.alpha = 1

        def Color(self, value):
            self.color = value
            return self
        def Alpha(self, value):
            self.alpha = value
            return self
        def Size(self, value):
            self.size = value
            return self
        def Style(self, value):
            self.style = value
            return self
        def Step(self, value):
            self.step = value
            return self
        
    class Label:
        """
        Defines Label-Styling and Text. Universal.\\
        Attributes are:\\
        Text()\\
        Unit()\\
        Color()\\
        Fontsize()\\
        String() - Returns the String Representation
        """
        def __init__(self, text = "", latex = False):
            self.text = text
            self.text_latex = latex
            self.color = "black"
            self.fontsize = 16
            self.unit = ""
            self.unit_latex = True
            self.unit_brackets = True

        def Text(self, value, latex = False):
            self.text = value
            self.text_latex = latex
            return self

        def Unit(self, value, latex = True, brackets = True):
            self.unit = value
            self.unit_latex = latex
            self.unit_brackets = brackets
            return self

        def Color(self, value):
            self.color = value
            return self
        
        def Fontsize(self, value):
            self.fontsize = value
            return self

        def String(self):
            string = ""
            if self.text_latex:
                string = f'$\\mathrm{{{self.text}}}$'
            else:
                string = self.text
            if self.unit != "" and self.unit is not None:
                if self.unit_latex and self.unit_brackets:
                    string = f'{string} [$\\mathrm{{{self.unit}}}$]'
                elif self.unit_latex and not self.unit_brackets:
                    string = f'{string} $\\mathrm{{{self.unit}}}$'
                elif self.unit_brackets and not self.unit_latex:
                    string = f'{string} [{self.unit}]'
                else:
                    string = f'{string} {self.unit}'
            return string
        
    class TickTicker:
        def __init__(self):
            self = self.DefaultMajor()


        def DefaultMajor(self):
            self.length = 8
            self.width = 1
            self.color = "black"
            self.direction = "inout"
            return self
        
        def DefaultMinor(self):
            self.length = 4
            self.width = 1
            self.color = "black"
            self.direction = "inout"
            return self
        
        def Length(self, value):
            self.length = value
            return self
        def Width(self, value):
            self.width = value
            return self
        def Color(self, value):
            self.color = value
            return self
        def Direction(self, value):
            self.direction = value
            return self
        
    class TickGrid:
        def __init__(self):
            self = self.DefaultMajor()
        
        def DefaultMajor(self):
            self.color = "gray"
            self.alpha = 0.25
            self.linewidth = 1
            self.linestyle = "-"
            return self
        
        def DefaultMinor(self):
            self.color = "gray"
            self.alpha = 0.2
            self.linewidth = 0.6
            self.linestyle = "--"
            return self

        def Color(self, value):
            self.color = value
            return self
        def Alpha(self, value):
            self.alpha = value
            return self
        def Width(self, value):
            self.linewidth = value
            return self
        def Style(self, value):
            self.linestyle = value
            return self

    class ColorCycler:
        def __init__(self):
            self.colors = [f'C{i}' for i in range(0,10)]
            self.counter = 0
        def increase(self):
            if self.counter < 9:
                self.counter = self.counter +1
            else:
                self.counter = 0
        def GetCurrent(self):
            return self.colors[self.counter]
        def GetCurrentAndCycle(self):
            color = self.colors[self.counter]
            self.increase()
            return color
        
    class Objects:
        class Vector:
            """
            Defines a Vector to be used in a Plots 'OBJECTS'\\
            Attributes are:\\
            Vector() - Sets the Vector as an 2-Dim np.ndarray. Length will be scaled to length of input vector\\
            Rad() - Sets the Vector for the input angle in radians. Keeps current length\\
            Deg() - Sets the Vector for the input angle in degree. Keeps current length\\
            Length() - Sets length. Unit may be arbitrary\\
            Origin() - Sets the origin coordinates.\\
            Color()\\
            Width()\\
            Headwidth()\\
            Headlenght()\\
            """
            def __init__(self, vector: np.ndarray = np.ndarray([0,0])):
                self.length = np.linalg.norm(vector)
                if self.length != 0:
                    self.vector = vector/self.length
                else:
                    self.vector = vector
                self.origin = (0,0)

                self.width = 1
                self.headwidth = 2
                self.headlength = 2

                self.color = None
                self.alpha = 1

                self.mirror = False


            def Vector(self, value):
                self.vector = value
                self.length = np.linalg.norm(self.vector)
                return self
            def Rad(self, angle, length=None):
                if length:
                    self.length = length
                self.vector = np.array([np.cos(angle), np.sin(angle)])
                return self
            def Deg(self, angle, length=None):
                if length:
                    self.length = length
                angle = angle/360*2*np.pi
                self.vector = 5*np.array([np.cos(angle), np.sin(angle)])
                return self
            def Length(self, value):
                self.length = value
                return self
            def Origin(self, x, y):
                self.origin = (x, y)
                return self
            def Color(self, value):
                self.color = value
                return self
            def Alpha(self, value):
                self.alpha = value
                return self
            def Width(self, value):
                self.width = value
                return self
            def HeadWidth(self, value):
                self.headwidth = value
                return self
            def HeadLength(self, value):
                self.headlength = value
                return self
            def Mirror(self, value=True):
                self.mirror = value
                return self

    @staticmethod
    def Plot(config: dict, graphs:list[dict], objects: list[dict] | None = None):
        """
        Creates a Graph-Plot based on the Config and Graphs given:
        - data: DataFrame or List of Lists
        - config: Config Dictionary
        - graphs: List of Dictionary for Graphs to be plotted
        - objects: Optional, List of Dictionary for Objects (Labels, Vectors etc.) to be plotted
        
        Example Plot-Config can be found here: https://1.1.1.1 or printed with Plotter.Config("plot"), Plotter.MinimalConfig("plot") or Plotter.FullConfig("plot")\\
        Example Graph-Config can be found here: https://1.1.1.1 or printed with Plotter.Config("graph"), Plotter.MinimalConfig("graph") or Plotter.FullConfig("graph")\\
        Example Object-Config can be found here: https://1.1.1.1 or printed with Plotter.Config("object"), Plotter.MinimalConfig("object") or Plotter.FullConfig("object")
        """

        if objects is None:
            objects = []

        

        plot_conf = config.get("plot", {})
        plot_size = plot_conf.get("plotsize", (10,10))
        filename = plot_conf.get("filename", None)

        x_axis_conf = config.get("x-axis", {})
        y_axis_conf = config.get("y-axis", {})

        Log = BoolLogger()
        Log.Set(plot_conf.get("logging", False))
        fig, ax = plt.subplots(figsize=plot_size)

        # Achsenbeschriftungen inkl. Einheiten (Latex-Formatierung möglich)
        title = plot_conf.get("title", Plotter.Label("Plot"))
        if isinstance(title, str):
            pass
        elif isinstance(title, Plotter.Label):
            title = title.String()
        xlabel = x_axis_conf.get("label", Plotter.Label("x-Axis"))
        ylabel = y_axis_conf.get("label", Plotter.Label("y-Axis"))
        ax.set_title(title, fontsize=xlabel.fontsize, color=xlabel.color)
        ax.set_xlabel(xlabel.String(), fontsize=xlabel.fontsize, color=xlabel.color)
        ax.set_ylabel(ylabel.String(), fontsize=ylabel.fontsize, color=ylabel.color)

        ColorCyler = Plotter.ColorCycler()

        for i, graph_config in enumerate(graphs):
            graph_label = graph_config.get("label", Plotter.Label(f"Graph {i}")).String()
            graph_data = graph_config.get("data", None)
            if graph_data is None:
                print(f"Skipping {graph_label}, Data is None")

            if isinstance(graph_data, Plotter.Graph):
                #Values for Graph Instance
                mask= CreateMask(graph_data.x_values, graph_data.x_range)
                x_values_plot = graph_data.x_values[mask]
                y_values_plot = graph_data.y_values[mask]
                mask= CreateMask(y_values_plot, graph_data.y_range)
                x_values_plot = x_values_plot[mask]
                y_values_plot = y_values_plot[mask]
                
                        #Style for Graph Instance
                graph_linestyling = graph_config.get("line-styling", Plotter.Line())
                graph_markerstyling = graph_config.get("marker-styling", Plotter.Marker().Style(""))
                if graph_linestyling.color is None:
                    graph_linestyling.color = ColorCyler.GetCurrentAndCycle()
                    if graph_markerstyling.color is None:
                        graph_markerstyling.color = graph_linestyling.color
                elif graph_markerstyling.color is None:
                    graph_markerstyling.color = graph_linestyling.color

                #Plot
                ax.plot(x_values_plot, y_values_plot, label=graph_label, color=graph_linestyling.color, linewidth = graph_linestyling.width, linestyle=graph_linestyling.style ,marker=graph_markerstyling.style, markerfacecolor=graph_markerstyling.color, markersize=graph_markerstyling.size, zorder=graph_data.z)
                if graph_data.x_mirror:
                    ax.plot(-x_values_plot, y_values_plot, label=None, color=graph_linestyling.color, linewidth = graph_linestyling.width, linestyle=graph_linestyling.style ,marker=graph_markerstyling.style, markerfacecolor=graph_markerstyling.color, markersize=graph_markerstyling.size, zorder=graph_data.z)
                if graph_data.y_mirror:
                    ax.plot(x_values_plot, -y_values_plot, label=None, color=graph_linestyling.color, linewidth = graph_linestyling.width, linestyle=graph_linestyling.style ,marker=graph_markerstyling.style, markerfacecolor=graph_markerstyling.color, markersize=graph_markerstyling.size, zorder=graph_data.z)
                #Fits
                for fit in graph_config.get("fits", []):
                    fit_label = fit.get("label", "")
                    fit_type = fit.get("type", None)
                    fit_range = fit.get("fit-range", None)
                    fit_plot_range = fit.get("plot-range", None)
                    fit_function = None
                    popt = None

                    if fit_type is None:
                        continue
                    mask = CreateMask(graph_data.x_values, fit_range)
                    x_values_fit = graph_data.x_values[mask]
                    y_values_fit = graph_data.y_values[mask]
                    print("FIT:", len(x_values_fit))

                    if fit_type.lower() in ["lin", "linear"]:
                        print(f'Linear Fit for Graph "{graph_label}"')
                        def fit_linear(x, A, B):
                            return A*x + B
                        popt, pcov = scipy.optimize.curve_fit(fit_linear, x_values_fit, y_values_fit)
                        print(f'Fit Paramter for {graph_config.get("label", "")}/{fit_label}: {popt}')
                        fit_function = fit_linear
                        
                    elif fit_type.lower() in ["gauss", "gaus"]:

                        A_0 = np.max(y_values_fit)
                        mu_0 = (x_values_fit[-1] + x_values_fit[0])/2
                        sigma_0 = (x_values_fit[-1] - x_values_fit[0])/3
                        C_0 = np.min(y_values_fit)
                        p0 = [A_0, mu_0, sigma_0, C_0]
                        print(f'Gauss Fit for Graph "{graph_label}"')
                        def fit_gauss(x, A, mu, sigma, C):
                            return A*np.exp(-1/2*((x-mu)**2)/(sigma**2)) + C
                        popt, pcov = scipy.optimize.curve_fit(fit_gauss, x_values_fit, y_values_fit, p0=p0)
                        print(f'Fit Paramter for {graph_config.get("label", "")}/{fit_label}: {popt}')
                        fit_function = fit_gauss
                    
                    mask = CreateMask(x_values_plot, fit_plot_range)
                    x_values_fit = x_values_plot[mask]
                    if fit.get("plot-step", None):
                        x_values_fit = np.arange(x_values_fit[0], x_values_fit[-1], fit.get("plot-step", None))
                    style_args = {
                        "color": fit.get("line-color", None),
                        "linewidth": fit.get("line-size", 1),
                        "linestyle": fit.get("line-style", "--"),
                    }
                    if popt is not None:
                        ax.plot(x_values_fit, fit_function(x_values_fit, *popt), **style_args)
                        if fit.get("marker", "") != "" and fit.get("marker", "") is not None:
                            style_args = {
                                "linewidth": fit.get("marker-width", 1),
                                "linestyle": "",
                                "marker": fit.get("marker", ""),
                                "markerfacecolor": fit.get("marker-color", None),
                                "markersize": fit.get("marker-size", 1),
                                "markeredgewidth": fit.get("marker-width", 1),
                            }
                            if fit.get("marker-step", None):
                                x_values_fit = np.arange(x_values_fit[0], x_values_fit[-1], fit.get("marker-step", None))

                            ax.plot(x_values_fit, fit_function(x_values_fit, *popt), **style_args)
                    else:
                        print(f'Invalid popt "{popt}" for {fit_type}-Fit "{fit_label}" on "Graph {graph_label}"')

            if isinstance(graph_data, Plotter.Scatter):
                mask_x = CreateMask(graph_data.x_values, graph_data.x_range)
                mask_y = CreateMask(graph_data.y_values[mask_x], graph_data.y_range)

                markerstyling = graph_config.get("marker", Plotter.Marker())
                ax.scatter(graph_data.x_values[mask_x][mask_y], graph_data.y_values[mask_x][mask_y], zorder=graph_data.z, marker=markerstyling.style, color=markerstyling.color, s=markerstyling.size, alpha=markerstyling.alpha)


        ## Objects
        for i, obj in enumerate(objects):
            if isinstance(obj, Plotter.Objects.Vector):
                ax.quiver(*obj.origin, *(obj.vector*obj.length),
                angles='xy', scale_units='xy',
                scale=1, color=obj.color, alpha=obj.alpha,
                width=obj.width/1000,
                headwidth=obj.headwidth, headlength=obj.headlength
                )
                if obj.mirror:
                    ax.quiver(*obj.origin, *(-obj.vector*obj.length),
                    angles='xy', scale_units='xy',
                    scale=1, color=obj.color, alpha=obj.alpha,
                    width=obj.width/1000,
                    headwidth=obj.headwidth, headlength=obj.headlength
                    )
                Log.Print("Plotted Vector")


        ## Axes
        # Ticks, Tick Labels and Grid
        grid_conf = x_axis_conf.get("major-grid", Plotter.TickGrid().DefaultMajor())
        label_conf = x_axis_conf.get("major-label", Plotter.Label())
        tick_conf = x_axis_conf.get("major-ticker", Plotter.TickTicker().DefaultMajor())
        ax.tick_params(which="major", axis="x", labelcolor = label_conf.color, labelsize = label_conf.fontsize, direction=tick_conf.direction, length=tick_conf.length, width=tick_conf.width, color=tick_conf.color)
        ax.grid(which="major", axis="x", color = grid_conf.color, alpha=grid_conf.alpha, linewidth=grid_conf.linewidth, linestyle=grid_conf.linestyle)

        grid_conf = x_axis_conf.get("minor-grid", Plotter.TickGrid().DefaultMinor())
        label_conf = x_axis_conf.get("minor-label", Plotter.Label())
        tick_conf = x_axis_conf.get("minor-ticker", Plotter.TickTicker().DefaultMinor())
        ax.tick_params(which="minor", axis="x", labelcolor = label_conf.color, labelsize = label_conf.fontsize, direction=tick_conf.direction, length=tick_conf.length, width=tick_conf.width, color=tick_conf.color)
        ax.grid(which="minor", axis="x", color = grid_conf.color, alpha=grid_conf.alpha, linewidth=grid_conf.linewidth, linestyle=grid_conf.linestyle)

        grid_conf = y_axis_conf.get("major-grid", Plotter.TickGrid().DefaultMajor())
        label_conf = y_axis_conf.get("major-label", Plotter.Label())
        tick_conf = y_axis_conf.get("major-ticker", Plotter.TickTicker().DefaultMajor())
        ax.tick_params(which="major", axis="y", labelcolor = label_conf.color, labelsize = label_conf.fontsize, direction=tick_conf.direction, length=tick_conf.length, width=tick_conf.width, color=tick_conf.color)
        ax.grid(which="major", axis="y", color = grid_conf.color, alpha=grid_conf.alpha, linewidth=grid_conf.linewidth, linestyle=grid_conf.linestyle)

        grid_conf = y_axis_conf.get("minor-grid", Plotter.TickGrid().DefaultMinor())
        label_conf = y_axis_conf.get("minor-label", Plotter.Label())
        tick_conf = y_axis_conf.get("minor-ticker", Plotter.TickTicker().DefaultMinor())
        ax.tick_params(which="minor", axis="y", labelcolor = label_conf.color, labelsize = label_conf.fontsize, direction=tick_conf.direction, length=tick_conf.length, width=tick_conf.width, color=tick_conf.color)
        ax.grid(which="minor", axis="y", color = grid_conf.color, alpha=grid_conf.alpha, linewidth=grid_conf.linewidth, linestyle=grid_conf.linestyle)

        
        
        # Limits and Scales
        if x_axis_conf.get("limits", None):
            if x_axis_conf.get("limits")[0] > x_axis_conf.get("limits")[1]:
                print("x-limit start is larger than end")
            else:
                ax.set_xlim(x_axis_conf.get("limits"))
        if y_axis_conf.get("limits", None):
            ax.set_ylim(y_axis_conf.get("limits"))

        # Ticks
        x_major_ticks = x_axis_conf.get("major-ticks", None)
        if isinstance(x_major_ticks, (tuple, list)):
            ax.xaxis.set_major_locator(FixedLocator(x_major_ticks))
        elif isinstance(x_major_ticks, int):
            min, max = ax.get_xlim()
            ax.xaxis.set_major_locator(FixedLocator(np.linspace(min, max, x_major_ticks, endpoint=True)))
        elif isinstance(x_major_ticks, float):
            ax.xaxis.set_major_locator(MultipleLocator(x_major_ticks))
        else:
            pass
            
        x_minor_ticks = x_axis_conf.get("minor-ticks", None)
        if isinstance(x_minor_ticks, (tuple, list)):
            ax.xaxis.set_minor_locator(FixedLocator(x_minor_ticks))
        elif isinstance(x_minor_ticks, int):
            min, max = ax.get_xlim()
            ax.xaxis.set_minor_locator(FixedLocator(np.linspace(min, max, x_minor_ticks, endpoint=True)))
        elif isinstance(x_minor_ticks, float):
            ax.xaxis.set_minor_locator(MultipleLocator(x_minor_ticks))
        else:
            pass

        y_major_ticks = y_axis_conf.get("major-ticks", None)
        if isinstance(y_major_ticks, (tuple, list)):
            ax.yaxis.set_major_locator(FixedLocator(y_major_ticks))
        elif isinstance(y_major_ticks, int):
            min, max = ax.get_ylim()
            ax.yaxis.set_minor_locator(FixedLocator(np.linspace(min, max, y_major_ticks, endpoint=True)))
        elif isinstance(y_major_ticks, float):
            ax.yaxis.set_major_locator(MultipleLocator(y_major_ticks))
        else:
            pass

        y_minor_ticks = y_axis_conf.get("minor-ticks", None)
        if isinstance(y_minor_ticks, (tuple, list)):
            ax.yaxis.set_minor_locator(FixedLocator(y_minor_ticks))
        elif isinstance(y_minor_ticks, int):
            min, max = ax.get_ylim()
            ax.yaxis.set_minor_locator(FixedLocator(np.linspace(min, max, y_minor_ticks, endpoint=True)))
        elif isinstance(y_minor_ticks, float):
            ax.yaxis.set_minor_locator(MultipleLocator(y_minor_ticks))
        else:
            pass

        #ax.set_xscale(x_axis_conf.get("scale", "linear"))
        ##ax.set_yscale(y_axis_conf.get("scale", "linear"))

        #Legend
        Legend = plot_conf.get("legend", Plotter.Legend())
        if Legend.show:
            ax.legend(loc=Legend.position)

        # Plotting
        plt.tight_layout()
        if filename and filename != "":
            dpi = plot_conf.get("dpi", 100)
            plt.savefig(filename, dpi=dpi)
        plt.show()



def CreateMask(data, limits: tuple):
    if limits is None or limits == (None, None):
        return [True for i in range(0, len(data))]
    elif isinstance(limits[0], (float, int)) and isinstance(limits[1], (float, int)):
        return (data >= limits[0]) & (data <= limits[1])
    elif isinstance(limits[0], (float, int)):
        return (data >= limits[0]) & (data <= np.inf)
    elif isinstance(limits[1], (float, int)):
        return (data >= -np.inf) & (data <= limits[1])
    print(f"INVALID LIMITS FOR MASK: {limits}")
    return [True for i in range(0, len(data))]


class BoolLogger:
    def __init__(self):
        self.log = True

    def Set(self, value):
        self.log = value

    def Print(self, value):
        if self.log:
            print(value)