import supervised_retrieval
from xuv_spectrum import spectrum
import tensorflow as tf
import pickle
import numpy as np
import tf_functions
from phase_parameters import params
import measured_trace.get_trace as get_measured_trace
import generate_data3
import matplotlib.pyplot as plt


def calc_fwhm(tmat, I_t):
    half_max = np.max(I_t)/2
    index1 = 0
    index2 = len(I_t) - 1

    while I_t[index1] < half_max:
        index1 += 1
    while I_t[index2] < half_max:
        index2 -= 1

    t1 = tmat[index1]
    t2 = tmat[index2]
    fwhm = t2 - t1
    return fwhm, t1, t2, half_max

def run_retrievals_on_networks():
    # use one of the networks to retrieve the measured trace
    measured_trace = get_measured_trace.trace
    # supervised_retrieval_obj = supervised_retrieval.SupervisedRetrieval("MLMRL_noise_resistant_net_angle_18")
    # retrieve_output = supervised_retrieval_obj.retrieve(measured_trace)

    # # get the reconstruction of the measured trace with known xuv xuv coefficients
    # reconstructed_trace = retrieve_output["trace_recons"]
    # orignal_retrieved_xuv_coefs = retrieve_output["xuv_retrieved"]

    # # add noise to reconstructed trace
    # count_num = 50
    # noise_trace_recons_added_noise = generate_data3.add_shot_noise(reconstructed_trace, count_num)

    # # delete the tensorflow graph
    # del supervised_retrieval_obj

    # input the reconstructed trace to all the networks and see the variation in the output
    retrieved_xuv_cl = []
    for tf_model in [ "MLMRL_noise_resistant_net_angle_1",
                    "MLMRL_noise_resistant_net_angle_2",
                    "MLMRL_noise_resistant_net_angle_3",
                    "MLMRL_noise_resistant_net_angle_4",
                    "MLMRL_noise_resistant_net_angle_5",
                    "MLMRL_noise_resistant_net_angle_6",
                    "MLMRL_noise_resistant_net_angle_7",
                    "MLMRL_noise_resistant_net_angle_8",
                    "MLMRL_noise_resistant_net_angle_9",
                    "MLMRL_noise_resistant_net_angle_10",
                    "MLMRL_noise_resistant_net_angle_11",
                    "MLMRL_noise_resistant_net_angle_12",
                    "MLMRL_noise_resistant_net_angle_13",
                    "MLMRL_noise_resistant_net_angle_14",
                    "MLMRL_noise_resistant_net_angle_15",
                    "MLMRL_noise_resistant_net_angle_16",
                    "MLMRL_noise_resistant_net_angle_17",
                    "MLMRL_noise_resistant_net_angle_18",
                    "MLMRL_noise_resistant_net_angle_19",
                    "MLMRL_noise_resistant_net_angle_20",
                    "MLMRL_noise_resistant_net_angle_21",
                    "MLMRL_noise_resistant_net_angle_22",
                    "MLMRL_noise_resistant_net_angle_23",
                    "MLMRL_noise_resistant_net_angle_24",
                    "MLMRL_noise_resistant_net_angle_25",
                    "MLMRL_noise_resistant_net_angle_26",
                    "MLMRL_noise_resistant_net_angle_27",
                    "MLMRL_noise_resistant_net_angle_28",
                    "MLMRL_noise_resistant_net_angle_29",
                    "MLMRL_noise_resistant_net_angle_30"
                    ]:
        supervised_retrieval_obj = supervised_retrieval.SupervisedRetrieval(tf_model)
        retrieve_output = supervised_retrieval_obj.retrieve(measured_trace)
        retrieved_xuv_coefs = retrieve_output["xuv_retrieved"]
        del supervised_retrieval_obj

        # add the retrieved xuv coefs to list
        retrieved_xuv_cl.append(retrieved_xuv_coefs)

    data = {}
    data["retrieved_xuv_cl"] = retrieved_xuv_cl
    data["measured_trace"] = measured_trace
    # data["orignal_retrieved_xuv_coefs"] = orignal_retrieved_xuv_coefs
    # return retrieved_xuv_cl, noise_trace_recons_added_noise, orignal_retrieved_xuv_coefs
    return data



if __name__ == "__main__":
    """
    this .py file is for taking many trained networks and retrieving the measured trace and a
    reconstruction of the measured trace (then having known xuv coefficients) and performing
    multiple retrievals with many trained networks to look at the variation in retrieval
    """

    # data = run_retrievals_on_networks()
    # with open("multiple_net_retrieval_test.p", "wb") as file:
    #     pickle.dump(data, file)

    with open("multiple_net_retrieval_test.p", "rb") as file:
        obj = pickle.load(file)

    # create tensorflow graph
    xuv_coefs_in = tf.placeholder(tf.float32, shape=[None, params.xuv_phase_coefs])
    xuv_E_prop = tf_functions.xuv_taylor_to_E(xuv_coefs_in)
    with tf.Session() as sess:

        # convert to complex E
        first_iteration = True
        for xuv_coefs in obj["retrieved_xuv_cl"]:
            out = sess.run(xuv_E_prop, feed_dict={xuv_coefs_in:xuv_coefs})

            if first_iteration:
                E_t_vecs = np.array(out["t_photon"])
                E_f_vecs = np.array(out["f_photon_cropped"])
                first_iteration = False
            else:
                E_t_vecs = np.append(E_t_vecs, out["t_photon"], axis=0)
                E_f_vecs = np.append(E_f_vecs, out["f_photon_cropped"], axis=0)

        # get the t and f vectors for the actual (original retrieved pulse)
        # out = sess.run(xuv_E_prop, feed_dict={xuv_coefs_in:obj["orignal_retrieved_xuv_coefs"]})
        # E_t_vec_actual = out["t_photon"]
        # E_f_vec_actual = out["f_photon_cropped"]

    # plot the E_t and E_f vectors
    fig = plt.figure(figsize=(12,8))
    fig.subplots_adjust(hspace=0.3, left=0.1, right=0.9, top=0.9, bottom=0.1)
    gs = fig.add_gridspec(2, 3)
    ax = fig.add_subplot(gs[0,0])
    ax.pcolormesh(params.delay_values_fs, params.K, obj["measured_trace"], cmap="jet")
    ax.set_title("Input Trace")

    # # actual E(t)
    # ax = fig.add_subplot(gs[0,1])
    # I_t_actual = (np.abs(E_t_vec_actual)**2)[0]
    # ax.plot(spectrum.tmat_as, I_t_actual, color="black")
    # # calculate pulse duration
    # fwhm, t1, t2, half_max = calc_fwhm(spectrum.tmat_as, I_t_actual)
    # ax.plot([t1, t2], [half_max, half_max], color="blue")
    # ax.text(0.8, 0.8, "FWHM: %.0f as" % fwhm, backgroundcolor="cyan", transform=ax.transAxes, ha="center")

    # # temporal phase plotting
    # # axtwin = ax.twinx()
    # # axtwin.plot(spectrum.tmat_as, np.unwrap(np.angle(E_t_vec_actual[0])), color="green")
    # ax.set_yticks([])
    # ax.set_title("I(t) (Photon) actual")

    # predicted E(t)
    ax = fig.add_subplot(gs[1,1])
    I_t_vecs = np.abs(E_t_vecs)**2
    I_t_avg = np.mean(I_t_vecs, axis=0)
    ax.plot(spectrum.tmat_as, I_t_avg, color="black")
    # calculate pulse duration for mean
    fwhm, t1, t2, half_max = calc_fwhm(spectrum.tmat_as, I_t_avg)
    ax.plot([t1, t2], [half_max, half_max], color="blue")
    ax.text(0.9, 0.8, "FWHM: %.0f as" % fwhm, backgroundcolor="cyan", transform=ax.transAxes, ha="center")
    # calculate pulse duration for all the pulses
    pulse_durations = [] # all of the pulse durations [as]
    for I_t_vec in I_t_vecs:
        fwhm, t1, t2, half_max = calc_fwhm(spectrum.tmat_as, I_t_vec)
        pulse_durations.append(fwhm)

    pulse_durations = np.array(pulse_durations)

    # np.min(pulse_durations)
    # np.max(pulse_durations)
    # np.std(pulse_durations)
    ax.text(0.9, 0.7, "min: %.0f as" % np.min(pulse_durations), backgroundcolor="cyan", transform=ax.transAxes, ha="center")
    ax.text(0.9, 0.6, "max: %.0f as" % np.max(pulse_durations), backgroundcolor="cyan", transform=ax.transAxes, ha="center")
    ax.text(0.9, 0.5, "standard dev: %.0f as" % np.std(pulse_durations), backgroundcolor="cyan", transform=ax.transAxes, ha="center")


    ax.set_title("mean I(t) (Photon) retrieved\n (30 trained networks)")
    ax.set_xlabel("time [as]")
    ax.set_yticks([])

    # # actual E(f)
    # ax = fig.add_subplot(gs[0,2])
    # ax.plot(spectrum.fmat_hz_cropped, np.abs(E_f_vec_actual[0])**2, color="black")
    # ax.set_yticks([])
    # axtwin = ax.twinx()
    # axtwin.plot(spectrum.fmat_hz_cropped, np.unwrap(np.angle(E_f_vec_actual[0])), color="green")
    # axtwin.tick_params(axis='y', colors='green')
    # axtwin.set_ylabel("phase")
    # axtwin.yaxis.label.set_color("green")
    # ax.set_title("I(f) (Photon) actual")

    # predicted E(f)
    ax = fig.add_subplot(gs[1,2])
    I_f_vecs = np.abs(E_f_vecs)**2
    avg_I_f_vecs = np.mean(I_f_vecs, axis=0)
    phase_angle = np.unwrap(np.angle(E_f_vecs))
    avg_phase_angle = np.mean(phase_angle, axis=0)
    std_phase_angle = np.std(phase_angle, axis=0)

    ax.plot(spectrum.fmat_hz_cropped, avg_I_f_vecs, color="black")
    ax.set_yticks([])
    axtwin = ax.twinx()
    # axtwin.plot(spectrum.fmat_hz_cropped, np.unwrap(np.angle(avg_I_f_vecs)), color="green")
    axtwin.plot(spectrum.fmat_hz_cropped, avg_phase_angle, color="green")

    # draw standard deviation lines
    label_def = False
    for avg_phase_angle_c, std_phase_angle_c, f_c in zip(avg_phase_angle[::20], std_phase_angle[::20], spectrum.fmat_hz_cropped[::20]):
        # draw a line at this point
        if not label_def:
            axtwin.plot([f_c, f_c], [avg_phase_angle_c-(std_phase_angle_c/2), avg_phase_angle_c+(std_phase_angle_c/2)], color="black", label="standard\ndeviation")
            label_def = True
        else:
            axtwin.plot([f_c, f_c], [avg_phase_angle_c-(std_phase_angle_c/2), avg_phase_angle_c+(std_phase_angle_c/2)], color="black")
    axtwin.legend(loc=1)
    axtwin.set_ylabel("average phase")
    axtwin.yaxis.label.set_color("green")
    axtwin.tick_params(axis='y', colors='green')

    ax.set_title("mean I(f) (Photon) retrieved\n (30 trained networks)")
    ax.set_xlabel("frequency [Hz]")

    # plt.show()
    plt.savefig("./stdev_test_photon_measured_30traces.png")



