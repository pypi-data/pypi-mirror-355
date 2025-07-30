import numpy as np
from scipy.stats import kendalltau
from sklearn.neighbors import KDTree as KDTree_whole
from scipy.spatial import KDTree as KDTree_layer
from sklearn.decomposition import NMF
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import random
from scipy import stats
from scipy.stats import hypergeom


class ComparisonTree:
    def __init__(
        self,
        cond1,
        ras_data,
        metaData_RAS_column,
        rss_data,
        colnames,
        rownames,
        threshold_file,
    ):
        """Constructor

        Args:
            cond1 (str): control treatments
            ras_data (pandas.DataFrame): AUCell matrix and metadata
            metaData_RAS_column (list): cell cluster
            rss_data (pandas.DataFrame): RSS matrix
            colnames (list): clusters of interest
            rownames (list): rownames of each of your regulons
            threshold_file (pandas.DataFrame): Calculated by SCENIC
        """
        self.cond1 = cond1
        self.data = rss_data
        self.RAS_AUC = ras_data
        self.labels = colnames
        self.sep = []
        self.map_me = {}
        self.NMF_embedd = {}
        self.h_sep = {}
        self.x = self.data[self.cond1].tolist()
        self.label = list(
            map(lambda x: x.split(" ")[0], self.data[rownames].tolist())
        )  ## rownames of your regulons
        self.metaDataCol = metaData_RAS_column
        self.threshold_file = threshold_file
        self.order = []
        self.condition_label = []
        self.tau_p_value = {}

    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query_ball_tree.html
    def compareLayers(self, layer1, layer2, distance, font=6.5):
        """_summary_

        Compare between two different layers

        Args:
            layer1 (String): Cell Cluster 1
            layer2 (String): Cell Cluster 2
            distance (float): Distance to query
            font (float, optional): _description_. Defaults to 6.5.
        """
        plt.figure(figsize=(6, 6))
        cond1x, cond1y = self.NMF_embedd[layer1][0], self.NMF_embedd[layer1][1]
        cond2x, cond2y = (
            self.NMF_embedd[layer2][0],
            self.NMF_embedd[layer2][1],
        )  # you can compare multiple experiments here

        plt.plot(cond1x, cond1y, "xk", markersize=10, label=layer1)
        plt.plot(cond2x, cond2y, "og", markersize=10, label=layer2)

        compare_layers = self.NMF_embedd[layer1][4].query_ball_tree(
            self.NMF_embedd[layer2][4], r=distance
        )

        for i in range(len(compare_layers)):
            for j in compare_layers[i]:
                plt.plot([cond1x[i], cond2x[i]], [cond1y[i], cond2y[i]], "-b")

        for i in range(len(self.NMF_embedd[layer1][0])):
            plt.text(
                cond1x[i],
                cond1y[i],
                self.label[i],
                fontsize=font,
                ha="right",
                color="red",
            )

        for i in range(len(self.NMF_embedd[layer2][0])):
            plt.text(
                cond2x[i],
                cond2y[i],
                self.label[i],
                fontsize=font,
                ha="left",
                color="green",
            )

        plt.title("distance < {} between {} and {}".format(distance, layer1, layer2))
        plt.xlabel("NMF_base ({})".format(layer1))
        plt.ylabel("NMF_exp ({})".format(layer2))
        plt.legend()
        plt.savefig("Layer {} and {}".format(layer1, layer2))

        # Show the plot
        plt.show()

    def calc_global_dictonary(self):
        """_summary_
        Calculates dictionary for entire tree to query all cell clusters

        Returns:
            dict: Dictionary that describes spatial relationships to all different experimental groups

        """
        dict_label = list(np.array([self.label] * len(self.condition_label)).flatten())
        dict_label = list(
            zip(
                [self.cond1] * len(self.condition_label),
                self.condition_label,
                dict_label,
            )
        )
        Idx_embedd = {}
        i = 0
        for ctrl_ref, cond, regulon in dict_label:
            Idx_embedd[i] = ctrl_ref + "-" + cond + ":\t" + regulon
            i += 1
        return Idx_embedd  # this is the global dictionary where we can query the entire 3D structure

    def create_global_tree(self, leaf_size=10):  ## can be expensive
        """_summary_
        Calculates the KDtree for all experimental conditions

        Args:
            leaf_size (int, optional): Leaf size for Kdtree parameter. Defaults to 10.

        Returns:
            tuple: KDtree, dict
        """
        X, Y, Z = self.construct_3D_embedding()
        Idx_embedd = self.calc_global_dictonary()
        NMF_XYZ = np.column_stack(((X, Y, Z)))
        entire_tree = KDTree_whole(
            NMF_XYZ, leaf_size
        )  # query the entire tree structure! #scikit will leaarn the structure
        return entire_tree, Idx_embedd

    def compute_tau_and_kdtree(self):
        """_summary_
        Initialize the comparisons across baseline and different experimental treatments
        """
        for i in self.labels:
            y = self.data[i].tolist()
            tau, p_value = kendalltau(self.x, y)
            self.tau_p_value[i] = (tau, p_value)
            query_kdtree = KDTree_layer(np.column_stack((self.x, y)))
            cond1x, condy, test1, h = self.nmf_transform(np.array(list(zip(self.x, y))))
            self.h_sep[i] = h
            self.NMF_embedd[i] = (cond1x, condy, test1, tau, query_kdtree)
            self.sep.append(tau)

    def return_the_tau_pval(self):
        return self.tau_p_value

    def analyze_factors(self, cond2, percentages=False):
        """_summary_
            Returns the components matrix
        Args:
            cond2 (string): Experimental group name
            percentages (bool, optional): Row normalizes component per each row.
        """
        H = self.h_sep[cond2]

        def plotHeatmap(H):

            sns.heatmap(
                H,
                annot=True,
                cmap="YlGnBu",
                xticklabels=[self.cond1 + " (control)", cond2],
                yticklabels=[f"NMF_{i+1}" for i in range(H.shape[0])],
            )

            plt.title(
                "Percentages (H) with Vectors {} and {}".format(self.cond1, cond2)
                if percentages
                else "Coefficient Matrix (H) with Vectors {} and {}".format(
                    self.cond1, cond2
                )
            )
            plt.tight_layout()
            plt.savefig("{}_{}.png".format(self.cond1, cond2))
            plt.show()

        plt.figure(figsize=(8, 6))
        if percentages:
            components = []
            for i in H:
                components.append([item / sum(i) for item in i])
            plotHeatmap(np.array(components))
        else:
            plotHeatmap(H)

    def nmf_transform(self, rss_data):
        """_summary_
        NMF implemented here, sets random state = 42
        Args:
            rss_data (_type_): _description_
        Returns:
            tuple: W[0], W[1], W, H
        """
        n_components = 2  # Reduce to 2 components for visualization
        nmf = NMF(n_components=n_components, init="random", random_state=42)
        embedding = nmf.fit_transform(rss_data)
        H_matrix = nmf.components_
        return (embedding[:, 0], embedding[:, 1], embedding, H_matrix)

    def map_labels_to_tau(self):
        """_summary_
        Generate a tau as a hash for embedding comparison
        """
        for i, lbl in list(zip(self.sep, self.labels)):
            if i in self.map_me:  # Just in case we have the same tau value
                prev_value = self.map_me[i]
                print(lbl, "warning: has a dup")
                self.map_me[i] = (prev_value, lbl)
            else:
                self.map_me[i] = lbl  # Make the tau into a key

    def sort_and_print_labels(self):
        """_summary_
        Show the experimental groups with their corresponding hash value
        """
        self.sep = sorted(self.sep)
        for i in self.sep:
            print(self.map_me[i], i)

    def init_order(self):  ## how to construct the 3d embedding space
        """_summary_
        Construct the order of each layer (lowest -> highest) for 3D plane comparison
        """
        order = []
        condition_label = []

        ## make sure self.spe is sorted
        for i in sorted(list(set(self.sep))):
            if isinstance(self.map_me[i], str):
                # print("path A")
                order.append(self.map_me[i])
                # print(order)
            else:
                print("path B")
                for i in self.map_me[i]:
                    order.append(i)

        item = order[len(order) - 1]
        order = order[:-1]
        # print("getting rid of {}".format(item))
        # remove one from the top, this is after order is stacked here
        for i in order:
            print(i)
            condition_label.append([i] * len(self.label))

        self.order = order  # subtract the one here!
        self.condition_label = np.array(condition_label).flatten()

    def construct_3D_embedding(self, rawRSS=False):
        """_summary_
        Unify all components (X, Y, Z) from NMF calculation from each experimental group
        Args:
            rawRSS (bool, optional): Plot raw RSS values. Defaults to False.
        """
        X, Y, Z = [], [], []

        def prepare_data(data_source):
            """Helper function to prepare the data for plotting"""
            nonlocal X, Y, Z
            for i in self.order:
                x = (
                    data_source[self.cond1].tolist()
                    if rawRSS
                    else self.NMF_embedd[i][0]
                )
                y = data_source[i].tolist() if rawRSS else self.NMF_embedd[i][1]
                Z_val = [self.NMF_embedd[i][3]] * len(self.label)
                X.extend(x)
                Y.extend(y)
                Z.extend(Z_val)

        if rawRSS:
            prepare_data(self.data)
        else:
            prepare_data(self.NMF_embedd)

        # Convert lists to np.array and flatten them
        X = np.array(X).flatten()
        Y = np.array(Y).flatten()
        Z = np.array(Z).flatten()

        return (X, Y, Z)

    def initDict(self, label):
        dict = {}
        for i in range(len(label)):
            dict[i] = label[i]
        return dict

    def plot_3dEmbedding(self, rawRSS=False, regulonsToView=[], clustersToLabel=[]):
        """_summary_
        Plot on 3D space
        Args:
            rawRSS (bool, optional): Raw RSS values. Defaults to False.
            regulonsToView (list, optional): Pick which regulons to see what to change. Defaults to [].
            clustersToLabel (list, optional): Pick which experimental treatments to see labeled regulons. Defaults to [].
        """
        condition_color_map = {}
        for i in self.order:  # create the color mappings!
            color = f"#{random.randint(0, 0xFFFFFF):06x}"
            condition_color_map[i] = color

        X, Y, Z = self.construct_3D_embedding(rawRSS)

        # Create the figure and 3D axis
        fig = plt.figure(figsize=(15, 17))
        ax = fig.add_subplot(111, projection="3d")

        print(self.labels)
        dict = self.initDict(self.label)

        if len(clustersToLabel) == 0:
            clustersToLabel = list(set(self.condition_label))

        print(self.label)

        print(condition_color_map)

        if len(regulonsToView) > 0:
            for i in range(len(X)):
                item = dict[i % len(self.label)]
                if (
                    item in regulonsToView
                    and self.condition_label[i] in clustersToLabel
                ):
                    ax.text(
                        X[i],
                        Y[i],
                        Z[i],
                        s=str(item),
                        color=condition_color_map[self.condition_label[i]],
                        fontsize=12,
                        fontweight="bold",
                        style="italic",
                    )

        # Plot the data points for each condition
        for condition in np.unique(self.condition_label):
            mask = self.condition_label == condition
            ax.scatter(
                X[mask],
                Y[mask],
                Z[mask],
                color=condition_color_map[condition],
                label=condition,
            )

        # Set the labels and title
        ax.set_xlabel(f"RSS (control) {self.cond1}" if rawRSS else "NMF_1")
        ax.set_ylabel("RSS treatment" if rawRSS else "NMF_2")
        ax.set_zlabel("Kendall's Tau")
        ax.set_title(
            f"3D Plot of {self.cond1} vs Conditions with Kendall's Tau using NMF reduction"
            if not rawRSS
            else f"3D Plot of RSS scores {self.cond1} vs Conditions with Kendall's Tau"
        )

        # Add legend
        ax.legend()

        # Show the plot
        plt.show()

    def construct_tree(self):
        """_summary_
        Init class to map tau and assemble KDtree
        """
        self.compute_tau_and_kdtree()
        self.map_labels_to_tau()
        self.sort_and_print_labels()  # this is how the 3D embedding will be assembled
        self.init_order()  # we are assemling the tree!

    def plotRSS_NMF(
        self, cond2, drawQuadrants=True, include_pvals=False, alpha=0.05, tryLabel=""
    ):
        """_summary_

        Args:
            cond2 (String): Experimental group
            drawQuadrants (bool, optional): Draw quadrants to separate out regions. Defaults to True.
            include_pvals (bool, optional): Perform hypergeomtric testing. Defaults to False.
            alpha (float, optional): FDR rate. Defaults to 0.05.
            tryLabel (str, optional): _description_. Defaults to "".

        Returns:
            _type_: P-vals of hypergeomtric output of each regulon calculated
        """
        cond1x = self.NMF_embedd[cond2][0]
        condy = self.NMF_embedd[cond2][1]
        test1 = self.NMF_embedd[cond2][2]
        p_vals = {}

        def returnThreshold_dictionary(threshold_file, regulonC = None):
            thresholds, regulonNames, regulonThresholds = None, [], []
            
            if "3.5_" in threshold_file:
                thresholds = pd.read_csv(threshold_file, sep="\t").T
                regulonNames = list(map(lambda x: x.split(" ")[0], thresholds.loc["regulon"].tolist()))
                regulonThresholds = thresholds.loc[regulonC] # by the row.
            else:
                thresholds = pd.read_csv(threshold_file)
                regulonNames = list(map(lambda x: x.split(" ")[0], thresholds[regulonC]))
                regulonThreshold = thresholds[regulonC] # column must be named like this ...
                
            threshold_dict = {}
            
            for i in range(len(regulonNames)):
                threshold_dict[regulonNames[i]] = regulonThresholds[i]
                i += 1
            
            return threshold_dict

        plt.scatter(cond1x, condy)

        def rundifferential_test_AUC(
            df,
            metaClusterLabel,
            control,
            treatment,
            regulon_name,
            threshold_file,
            alpha=0.05,
        ):
            """
            Add a column to mark successful cells (greater than the mean enrichment score)
            M is the total number of objects,  (all the cells = total population (low and high regulon activity)
            n is total number of Type I objects.  (all cells that pass threshold)
            The random variate represents the number of Type I objects
            in N drawn without replacement from the total population.

            k is the active amount of cells we are interested in
            N the anumberof cells you are planning to sample from the tissue

            sf(k, M, n, N, loc=0)
            """
            df.columns = list(map(lambda x: x.split(" ")[0], df.columns))
            if threshold_file is None:
                calculate_mean = df[regulon_name].mean()
                df["is_successful_{}".format(regulon_name)] = (
                    df[regulon_name] > df[regulon_name].mean()
                )
            else:
                threshold = returnThreshold_dictionary(threshold_file, "threshold")
                df["is_successful_{}".format(regulon_name)] = (
                    df[regulon_name] > threshold[regulon_name]
                )

            # Count successful control cells
            control_successful_cells = df[
                (df[metaClusterLabel] == control)
                & (df["is_successful_{}".format(regulon_name)])
            ].shape[0]

            # Count successful treatment cells
            treatment_successful_cells = df[
                (df[metaClusterLabel] == treatment)
                & (df["is_successful_{}".format(regulon_name)])
            ].shape[0]
            total_successful_cells = df[
                df["is_successful_{}".format(regulon_name)]
            ].shape[0]

            total_population = df.shape[0]
            n_1 = df[df[metaClusterLabel] == control].shape[0]
            n_2 = df[df[metaClusterLabel] == treatment].shape[0]

            p_value_1 = hypergeom.sf(
                control_successful_cells - 1,
                total_population,
                total_successful_cells,
                n_1,
            )
            p_value_2 = hypergeom.sf(
                treatment_successful_cells - 1,
                total_population,
                total_successful_cells,
                n_2,
            )

            return (regulon_name, round(p_value_1, 2), round(p_value_2, 2))

        def drawText(cond1x, condy):
            i = 0
            for x_2, y_2 in list(zip(cond1x, condy)):
                text = self.label[i]
                if include_pvals:
                    # rundifferential_test_AUC(df, control, treatment, regulon_name, alpha = .05)
                    min_font_size = 6
                    max_font_size = 12

                    chk = self.threshold_file
                    _, _, p_value_treatment = rundifferential_test_AUC(
                        self.RAS_AUC, self.metaDataCol, self.cond1, cond2, text, chk
                    )

                    color = "red" if p_value_treatment < alpha else "black"

                    if color == "black":
                        font_size = min_font_size
                    else:
                        font_size = max(
                            min_font_size,
                            min(max_font_size, max_font_size / (p_value_treatment * 5)),
                        )

                    plt.text(
                        x_2,
                        y_2,
                        text,
                        ha="center",
                        va="bottom",
                        fontsize=font_size,
                        fontweight="bold",
                        color=color,
                    )  # the bigger the p_value, smaller text
                    p_vals[text] = p_value_treatment
                else:
                    plt.text(
                        x_2,
                        y_2,
                        text,
                        ha="center",
                        va="bottom",
                        fontsize=6.5,
                        fontweight="bold",
                    )
                i += 1

        drawText(cond1x, condy)
        # plt.title("NMF Embedding of RSS Values {} and {}".format(self.cond1, cond2))
        plt.xlabel("NMF_base ({})".format(self.cond1))
        plt.ylabel("NMF_exp ({})".format(cond2))

        if drawQuadrants:
            plt.axvline(x=np.median(cond1x), color="black", linestyle="--")
            plt.axhline(y=np.median(condy), color="black", linestyle="--")

        plt.savefig("{}_{}.png".format(self.cond1, cond2))
        plt.show()

        kmeans = KMeans(n_clusters=2, random_state=42)
        kmeans.fit(test1)
        plt.scatter(cond1x, condy, c=kmeans.labels_, cmap="viridis")
        t2 = drawText(cond1x, condy)

        if drawQuadrants:
            plt.axvline(x=np.median(cond1x), color="black", linestyle="--")
            plt.axhline(y=np.median(condy), color="black", linestyle="--")

        plt.title(
            "K-Means Clustering after NMF {} and {}".format(self.cond1, cond2),
            fontsize=8.5,
        )
        plt.xlabel("NMF_base {}".format(self.cond1))
        plt.ylabel("NMF_exp {}".format(cond2))
        # plt.savefig('{}_{}.png'.format(self.cond1,cond2))  # Save as PNG
        # plt.colorbar(label="Cluster Label")
        plt.show()

        return p_vals
