import tensorflow as tf
import numpy as np
import scipy.constants as sc
import matplotlib.pyplot as plt
import tables
import shutil
import os
import csv
import network3
from xuv_spectrum import spectrum
from phase_parameters import params
from ir_spectrum import ir_spectrum
import glob
import pickle
import tf_functions
import measured_trace.get_trace as get_measured_trace
import ga as genetic_alg
import unsupervised_retrieval


run_name = "measured_retrieval_init"
with open("./retrieval/" + run_name + "/plot_objs.p", "rb") as file:
    plot_obj = pickle.load(file)

# import ipdb; ipdb.set_trace() # BREAKPOINT


def plot_images_fields_publication(traces_meas, traces_reconstructed, xuv_f, xuv_f_phase,  xuv_f_full, xuv_t, ir_f, i,
                       run_name, true_fields=False, cost_function=None, method=None, save_data_objs=False):


    # create new axes
    fig = plt.figure(figsize=(10,7))
    gs = fig.add_gridspec(2,2)
    axes = dict()
    axes["input_trace"] = fig.add_subplot(gs[0,0])
    axes["reconstructed_trace"] = fig.add_subplot(gs[0,1])
    axes["xuv_t"] = fig.add_subplot(gs[1,1])
    axes["xuv_f"] = fig.add_subplot(gs[1,0])
    axes["xuv_f_phase"] = axes["xuv_f"].twinx()

    # ...........................
    # .....CALCULATE RMSE........
    # ...........................
    # calculate the rmse for each trace
    rmses = dict()
    for trace_type in ["trace", "autocorrelation", "proof"]:
        rmse = np.sqrt((1 / len(traces_meas[trace_type].reshape(-1))) * np.sum(
            (traces_meas[trace_type].reshape(-1) - traces_reconstructed[trace_type].reshape(-1)) ** 2))
        rmses[trace_type] = rmse

    # .......................................
    # .......................................
    # .......................................
    # ...............PLOTTING................
    # .......................................
    # .......................................
    # .......................................


    # just for testing
    # cost_function = "autocorrelation"
    # true_fields = False

    # ..........................................
    # ...............input traces...............
    # ..........................................
    axes["input_trace"].pcolormesh(params.delay_values_fs, params.K, traces_meas["trace"], cmap='jet')
    axes["input_trace"].set_xlabel(r"$\tau$ Delay [fs]")
    axes["input_trace"].set_ylabel("Energy [eV]")
    if true_fields:
        unsupervised_retrieval.normal_text(axes["input_trace"], (0.0, 1.0), "noisy trace")
    else:
        unsupervised_retrieval.normal_text(axes["input_trace"], (0.0, 1.0), "input trace")
        # if cost_function == "trace":
        #     unsupervised_retrieval.red_text(axes["input_trace"], (1.0, 1.0), "C")


    # ..........................................
    # ...............generated..................
    # ..........................................
    axes["reconstructed_trace"].pcolormesh(params.delay_values_fs, params.K, traces_reconstructed["trace"], cmap='jet')
    axes["reconstructed_trace"].set_xlabel(r"$\tau$ Delay [fs]")
    axes["reconstructed_trace"].set_ylabel("Energy [eV]")
    unsupervised_retrieval.normal_text(axes["reconstructed_trace"], (0.05, 0.05), "RMSE: "+"%.4f" % rmses["trace"])
    if true_fields:
        unsupervised_retrieval.normal_text(axes["reconstructed_trace"], (0.0, 1.0), "actual trace")
    else:
        unsupervised_retrieval.normal_text(axes["reconstructed_trace"], (0.0, 1.0), "generated trace")
        # if cost_function == "trace":
        #     unsupervised_retrieval.red_text(axes["reconstructed_trace"], (1.0, 1.0), "C")


    # xuv f
    fmat_hz = spectrum.fmat_cropped/sc.physical_constants['atomic unit of time'][0]*1e-17
    I_f = np.abs(xuv_f) ** 2
    axes["xuv_f"].plot(fmat_hz, I_f, color="black")
    axes["xuv_f"].set_yticks([])
    axes["xuv_f"].set_xlabel("Frequency [$10^{17}$Hz]")
    axes["xuv_f"].set_xlim(np.min(fmat_hz), np.max(fmat_hz))
    axes["xuv_f"].set_ylim(np.min(I_f), 1.2*np.max(I_f))
    # plotting photon spectrum
    axes["xuv_f"].plot(fmat_hz, np.abs(spectrum.Ef_photon[spectrum.indexmin:spectrum.indexmax]) ** 2, color="blue")


    if true_fields:
        axes["xuv_f_phase"].text(0.0, 1.1, "actual XUV spectrum", backgroundcolor="white",
                                         transform=axes["xuv_f_phase"].transAxes)
    else:
        axes["xuv_f_phase"].text(0.0, 1.1, "predicted XUV spectrum", backgroundcolor="white",
                                         transform=axes["xuv_f_phase"].transAxes)

    axes["xuv_f_phase"].tick_params(axis='y', colors='green')
    axes["xuv_f_phase"].plot(fmat_hz, -1*xuv_f_phase, color="green")


    # xuv predicted
    # xuv t
    # tmat_as = spectrum.tmat * sc.physical_constants['atomic unit of time'][0] * 1e18
    tmat_as = spectrum.tmat_as

    # from the electron spectrum
    # I_t = np.abs(xuv_t) ** 2

    # from photon spectrum
    angle = np.angle(xuv_f_full * np.exp(-2j*np.angle(xuv_f_full)))
    Ef_photon_phase = spectrum.Ef_photon * np.exp(1j * angle)
    Et_photon_phase = np.fft.fftshift(np.fft.fft(np.fft.fftshift(Ef_photon_phase)))
    I_t = np.abs(Et_photon_phase) ** 2

    axes["xuv_t"].plot(tmat_as, I_t, color="black")
    #calculate FWHM
    fwhm, t1, t2, half_max = unsupervised_retrieval.calc_fwhm(tmat=tmat_as, I_t=I_t)
    axes["xuv_t"].text(1.0, 0.9, "FWHM:\n %.2f [as]" % fwhm, color="red",
                            backgroundcolor="white", ha="center",
                            transform=axes["xuv_t"].transAxes)
    #plot FWHM
    axes["xuv_t"].plot([t1, t2], [half_max, half_max], color="red", linewidth=2.0)
    axes["xuv_t"].set_yticks([])
    axes["xuv_t"].set_xlim(-150, 260)
    axes["xuv_t"].set_ylim(0, 1.2*np.max(I_t))
    axes["xuv_t"].set_xlabel("time [as]")
    # axes["xuv_t"].set_xlim(-200, 300)

    if true_fields:
        axes["xuv_t"].text(0.0, 1.1, "actual XUV $I(t)$", backgroundcolor="white",
                                     transform=axes["xuv_t"].transAxes)
    else:
        axes["xuv_t"].text(0.0, 1.1, "predicted XUV $I(t)$", backgroundcolor="white",
                                     transform=axes["xuv_t"].transAxes)
    fig.savefig("./publication_plot.png")



plot_images_fields_publication(traces_meas=plot_obj["traces_meas"],
                        traces_reconstructed=plot_obj["traces_reconstructed"], 
                        xuv_f=plot_obj["xuv_f"],
                        xuv_f_phase=plot_obj["xuv_f_phase"], 
                        xuv_f_full=plot_obj["xuv_f_full"],
                        xuv_t=plot_obj["xuv_t"], ir_f=plot_obj["ir_f"], i=plot_obj["i"],
                        run_name=plot_obj["run_name"], true_fields=plot_obj["true_fields"],
                        cost_function=plot_obj["cost_function"],
                        method=plot_obj["method"])




# plt.show()


