import matplotlib.pyplot as plt
import argparse
import numpy as np
import mplhep as hep
from scipy import stats
from sklearn.metrics import roc_curve, roc_auc_score, auc

hep.style.use("CMS")
hep.cms.label(loc=0)


def handle_arrays(score_lbl_tensor, column=0):
    sig = score_lbl_tensor[score_lbl_tensor[:, 1] == 1]
    bkg = score_lbl_tensor[score_lbl_tensor[:, 1] == 0]

    sig_value = sig[:, column]
    bkg_value = bkg[:, column]

    return sig_value, bkg_value


def my_roc_auc(classes : np.ndarray,
               predictions : np.ndarray,
               weights : np.ndarray = None) -> float:
    """
    Calculating ROC AUC score as the probability of correct ordering
    """

    if weights is None:
        weights = np.ones_like(predictions)

    assert len(classes) == len(predictions) == len(weights)
    assert classes.ndim == predictions.ndim == weights.ndim == 1
    class0, class1 = sorted(np.unique(classes))

    data = np.empty(
            shape=len(classes),
            dtype=[('c', classes.dtype),
                   ('p', predictions.dtype),
                   ('w', weights.dtype)]
        )
    data['c'], data['p'], data['w'] = classes, predictions, weights

    data = data[np.argsort(data['c'])]
    data = data[np.argsort(data['p'], kind='mergesort')] # here we're relying on stability as we need class orders preserved

    correction = 0.
    # mask1 - bool mask to highlight collision areas
    # mask2 - bool mask with collision areas' start points
    mask1 = np.empty(len(data), dtype=bool)
    mask2 = np.empty(len(data), dtype=bool)
    mask1[0] = mask2[-1] = False
    mask1[1:] = data['p'][1:] == data['p'][:-1]
    if mask1.any():
        mask2[:-1] = ~mask1[:-1] & mask1[1:]
        mask1[:-1] |= mask1[1:]
        ids, = mask2.nonzero()
        correction = sum([((dsplit['c'] == class0) * dsplit['w'] * msplit).sum() *
                          ((dsplit['c'] == class1) * dsplit['w'] * msplit).sum()
                          for dsplit, msplit in zip(np.split(data, ids), np.split(mask1, ids))]) * 0.5

    weights_0 = data['w'] * (data['c'] == class0)
    weights_1 = data['w'] * (data['c'] == class1)
    cumsum_0 = weights_0.cumsum()

    return ((cumsum_0 * weights_1).sum() - correction) / (weights_1.sum() * cumsum_0[-1])

def plot_sig_bkg_distributions(
    score_lbl_tensor_train, score_lbl_tensor_test, dir, show
):
    # plot the signal and background distributions
    sig_score_train, bkg_score_train = handle_arrays(score_lbl_tensor_train, 0)
    sig_score_test, bkg_score_test = handle_arrays(score_lbl_tensor_test, 0)

    # get weights
    sig_weight_train, bkg_weight_train = handle_arrays(score_lbl_tensor_train, 2)
    sig_weight_test, bkg_weight_test = handle_arrays(score_lbl_tensor_test, 2)

    fig, ax = plt.subplots()
    sig_train = plt.hist(
        sig_score_train,
        weights=sig_weight_train,
        bins=30,
        range=(0, 1),
        histtype="step",
        label="Signal (training)",
        density=True,
        edgecolor="blue",
        facecolor="dodgerblue",
        fill=True,
        alpha=0.5,
    )
    bkg_train = plt.hist(
        bkg_score_train,
        weights=bkg_weight_train,
        bins=30,
        range=(0, 1),
        histtype="step",
        label="Background (training)",
        density=True,
        color="r",
        fill=False,
        hatch="\\\\",
    )

    max_bin = max(max(sig_train[0]), max(bkg_train[0]))
    # set limit on y-axis
    ax.set_ylim(top=max_bin * 1.5)

    legend_test_list = []
    for score, weight, color, label in zip(
        [sig_score_test, bkg_score_test],
        [sig_weight_test, bkg_weight_test],
        ["blue", "r"],
        ["Signal (test)", "Background (test)"],
    ):
        counts, bins, _ = plt.hist(
            score,
            weights=weight,
            bins=30,
            alpha=0,
            density=True,
            range=(0, 1),
        )
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        # NOTE: are the errors correct?
        # Calculate bin widths
        bin_widths = bins[1:] - bins[:-1]

        # Calculate counts per bin
        counts_per_bin = counts * len(score) * bin_widths

        # Calculate standard deviation per bin
        std_per_bin = np.sqrt(counts_per_bin)

        # Calculate error bars by rescaling standard deviation
        errors = std_per_bin / np.sum(counts_per_bin)

        legend_test_list.append(
            plt.errorbar(
                bin_centers,
                counts,
                yerr=errors,
                marker="o",
                color=color,
                label=label,
                linestyle="None",
            )
        )
    ks_statistic_sig, p_value_sig = stats.ks_2samp(sig_score_train, sig_score_test)
    ks_statistic_bkg, p_value_bkg = stats.ks_2samp(bkg_score_train, bkg_score_test)

    # print the KS test results on the plot
    plt.text(
        0.5,
        0.925,
        f"KS test: p-value (sig) = {p_value_sig:.2f}",
        fontsize=20,
        transform=plt.gca().transAxes,
    )
    plt.text(
        0.5,
        0.85,
        f"KS test: p-value (bkg) = {p_value_bkg:.2f}",
        fontsize=20,
        transform=plt.gca().transAxes,
    )

    # compute the AUC of the ROC curve
    # print("score_lbl_tensor_test", score_lbl_tensor_test)
    # roc_auc= roc_auc_score(score_lbl_tensor_test[:, 1], score_lbl_tensor_test[:, 0], sample_weight=score_lbl_tensor_test[:, 2])
    # # print the AUC on the plot
    # plt.text(
    #     0.5,
    #     0.75,
    #     f"AUC = {roc_auc:.2f}",
    #     fontsize=20,
    #     transform=plt.gca().transAxes
    # )

    plt.xlabel("DNN output")
    plt.ylabel("Normalized counts")
    plt.legend(
        loc="upper left",
        # loc="center",
        # bbox_to_anchor=(0.3, 0.9),
        fontsize=20,
        handles=[
            sig_train[2][0],
            legend_test_list[0],
            bkg_train[2][0],
            legend_test_list[1],
        ],
        frameon=False,
    )
    # plt.plot([0.09, 0.88], [8.35, 8.35], color="lightgray", linestyle="-", transform=plt.gca().transAxes)

    hep.cms.lumitext(
        "2022 (13.6 TeV)",
    )
    hep.cms.text(
        text="Simulation Preliminary",
        loc=0,
    )
    plt.savefig(f"{dir}/sig_bkg_distributions.png", bbox_inches="tight", dpi=300)
    if show:
        plt.show()


def plot_roc_curve(score_lbl_tensor_test, dir, show):
    # plot the ROC curve
    fig, ax = plt.subplots()
    print("score_lbl_tensor_test", score_lbl_tensor_test)

    fpr, tpr, _ = roc_curve(
        score_lbl_tensor_test[:, 1],
        score_lbl_tensor_test[:, 0],
        sample_weight=score_lbl_tensor_test[:, 2],
    )
    # roc_auc =auc(tpr, fpr)
    # for i in range(len(tpr)):
    #     for j in range(len(tpr)):
    #         # if tpr[i]==tpr[j] and i>j:
    #         #     print("same", tpr[i], tpr[j], fpr[i], fpr[j], i, j)
    #         if tpr[i]>tpr[j] and i<j:
    #             print("inverse", tpr[i], tpr[j], fpr[i], fpr[j], i, j)
    #     if i%100==0:
    #         print(i)


    roc_auc =roc_auc_score(score_lbl_tensor_test[:, 1], score_lbl_tensor_test[:, 0], sample_weight=abs(score_lbl_tensor_test[:, 2]))
    roc_auc =my_roc_auc(score_lbl_tensor_test[:, 1], score_lbl_tensor_test[:, 0], (score_lbl_tensor_test[:, 2]))
    plt.plot(tpr, fpr, label="ROC curve (AUC = %0.3f)" % roc_auc)
    plt.plot([0, 1], [0, 1], color="gray", linestyle="--")
    plt.xlabel("True positive rate")
    plt.ylabel("False positive rate")
    plt.legend(loc="upper left")
    hep.cms.lumitext(
        "2022 (13.6 TeV)",
    )
    hep.cms.text(
        text="Simulation Preliminary",
        loc=0,
    )
    plt.savefig(f"{dir}/roc_curve.png", bbox_inches="tight", dpi=300)
    if show:
        plt.show()


if __name__ == "__main__":
    # parse the arguments
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i", "--input-dir", default="score_lbls", help="Input directory", type=str
    )
    parser.add_argument(
        "-s", "--show", default=False, help="Show plots", action="store_true"
    )
    parser.print_help()
    args = parser.parse_args()

    input_file = f"{args.input_dir}/score_lbl_array.npz"

    # load the labels and scores from the train and test datasets from a .npz file
    score_lbl_tensor_train = np.load(input_file, allow_pickle=True)[
        "score_lbl_array_train"
    ]
    score_lbl_tensor_test = np.load(input_file, allow_pickle=True)[
        "score_lbl_array_test"
    ]

    # plot the signal and background distributions
    plot_sig_bkg_distributions(
        score_lbl_tensor_train, score_lbl_tensor_test, args.input_dir, args.show
    )

    plot_roc_curve(score_lbl_tensor_test, args.input_dir, args.show)
