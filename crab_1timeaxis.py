import matplotlib.pyplot as plt
import numpy as np
import scipy.constants as sc


# SI units for defining parameters
W = 1
cm = 1e-2
um = 1e-6
fs = 1e-15
atts = 1e-18

class XUV_Field():

    def __init__(self, N, tmax):

        # define parameters in SI units
        self.N = N
        # self.en0 = 20 * sc.eV # central energy
        # self.den0 = 75 * sc.eV #energy fwhm
        self.f0 = 80e15
        self.T0 = 1/self.f0 # optical cycle
        self.t0 = 20e-18 # pulse duration
        self.gdd = 0 * atts**2 # gdd
        self.gdd_si = self.gdd / atts**2
        self.tod = 0 * atts**3 # TOD
        self.tod_si = self.tod / atts**3

        #discretize
        self.tmax = tmax
        self.dt = self.tmax / N
        self.tmat = self.dt * np.arange(-N/2, N/2, 1)

        # discretize the streaking xuv field spectral matrix
        self.df = 1/(self.dt * N)
        self.fmat = self.df * np.arange(-N/2, N/2, 1)
        self.enmat = sc.h * self.fmat

        # convert to AU
        # self.en0 = self.en0 / sc.physical_constants['atomic unit of energy'][0]
        # self.den0 = self.den0 / sc.physical_constants['atomic unit of energy'][0]
        self.t0 = self.t0 / sc.physical_constants['atomic unit of time'][0]
        self.f0 = self.f0 * sc.physical_constants['atomic unit of time'][0]
        self.T0 = self.T0 / sc.physical_constants['atomic unit of time'][0]
        self.gdd = self.gdd / sc.physical_constants['atomic unit of time'][0]**2
        self.tod = self.tod / sc.physical_constants['atomic unit of time'][0]**3
        self.dt = self.dt / sc.physical_constants['atomic unit of time'][0]
        self.tmat = self.tmat / sc.physical_constants['atomic unit of time'][0]
        self.fmat = self.fmat * sc.physical_constants['atomic unit of time'][0]
        self.enmat = self.enmat / sc.physical_constants['atomic unit of energy'][0]

        # set up streaking xuv field in AU
        self.Et = np.exp(-2 * np.log(2) * (self.tmat/self.t0)**2 ) * np.exp(2j * np.pi * self.f0 * self.tmat)

        # add GDD to streaking XUV field
        Ef = np.fft.fftshift(np.fft.fft(np.fft.fftshift(self.Et)))
        Ef_prop = Ef * np.exp(1j * 0.5 * self.gdd * (2 * np.pi)**2 * (self.fmat - self.f0)**2)
        # plt.figure(98)
        # plt.plot(0.5 * self.gdd * (2 * np.pi)**2 * (self.fmat - self.f0)**2)

        # add TOD to streaking XUV field
        # plt.figure(99)
        # plt.plot(0.5 * self.tod * (2 * np.pi)**3 * (self.fmat - self.f0)**3)
        # plt.figure(100)
        # plt.plot(np.real(Ef_prop), color='blue')
        # plt.plot(np.imag(Ef_prop), color='red')
        Ef_prop = Ef_prop * np.exp(1j * 0.5 * self.tod * (2 * np.pi)**3 * (self.fmat - self.f0)**3)
        # plt.figure(101)
        # plt.plot(np.real(Ef_prop), color='blue')
        # plt.plot(np.imag(Ef_prop), color='red')

        self.Et = np.fft.fftshift(np.fft.ifft(np.fft.fftshift(Ef_prop)))


class IR_Field():

    def __init__(self, N, tmax):
        self.N = N
        # calculate parameters in SI units
        self.lam0 = 1.7 * um    # central wavelength
        self.f0 = sc.c/self.lam0    # carrier frequency
        self.T0 = 1/self.f0 # optical cycle
        self.t0 = 12 * fs # pulse duration
        self.ncyc = self.t0/self.T0
        self.I0 = 1e13 * W/cm**2

        # compute ponderomotive energy
        self.Up = (sc.elementary_charge**2 * self.I0) / (2 * sc.c * sc.epsilon_0 * sc.electron_mass * (2 * np.pi * self.f0)**2)

        # discretize time matrix
        self.tmax = tmax
        self.dt = self.tmax / N
        self.tmat = self.dt * np.arange(-N/2, N/2, 1)

        # discretize spectral matrix
        self.df = 1/(self.dt * N)
        self.fmat = self.df * np.arange(-N/2, N/2, 1)
        self.enmat = sc.h * self.fmat

        # convert units to AU
        self.t0 = self.t0 / sc.physical_constants['atomic unit of time'][0]
        self.f0 = self.f0 * sc.physical_constants['atomic unit of time'][0]
        self.T0 = self.T0 / sc.physical_constants['atomic unit of time'][0]
        self.Up = self.Up / sc.physical_constants['atomic unit of energy'][0]
        self.dt = self.dt / sc.physical_constants['atomic unit of time'][0]
        self.tmat = self.tmat / sc.physical_constants['atomic unit of time'][0]
        self.fmat = self.fmat * sc.physical_constants['atomic unit of time'][0]
        self.enmat = self.enmat / sc.physical_constants['atomic unit of energy'][0]

        # calculate driving amplitude in AU
        self.E0 = np.sqrt(4 * self.Up * (2 * np.pi * self.f0)**2)

        # set up the driving IR field amplitude in AU
        self.Et = self.E0 * np.exp(-2 * np.log(2) * (self.tmat/self.t0)**2) * np.cos(2 * np.pi * self.f0 * self.tmat)


class Med():

    def __init__(self):

        self.Ip = 24.587 * sc.electron_volt
        self.Ip = self.Ip / sc.physical_constants['atomic unit of energy'][0]


def calculate(tau_slice, p_slice, time, frequency_whole, items):

    # construct the delay axis for the XUV
    delay_axis = tau_slice.reshape(-1, 1) * frequency_whole.reshape(1, -1)

    # calculate fft of XUV signal
    xuv_fft = np.fft.fftshift(np.fft.fft(np.fft.fftshift(items['Exuv'])))

    # construct matrix of fft of XUV signal
    xuv_mat = np.ones_like(delay_axis) * xuv_fft.reshape(1, -1)

    # apply phase shift to delay XUV pulse
    xuv_shifted = xuv_mat * np.exp(-2j * np.pi * delay_axis)

    # transform back to temporal domain
    xuv_time_shifted = np.fft.fftshift(np.fft.ifft(np.fft.fftshift(xuv_shifted)))
    xuv_time_shifted = xuv_time_shifted.reshape(1, np.shape(xuv_time_shifted)[0], np.shape(xuv_time_shifted)[1])

    # calculate vector potential matrix
    A_int_mat = np.ones_like(xuv_time_shifted) * items['A_t_integ'].reshape(1, 1, -1)

    # multiply vector potential matrix by momentum
    p_A_int_mat = np.exp(1j * p_slice.reshape(-1, 1, 1) * A_int_mat)

    # kinetic energy
    K = (0.5 * p_slice**2).reshape(-1, 1, 1)

    # fft exponential term
    e_fft = np.exp(-1j * (K + items['Ip']) * time.reshape(1, 1, -1))

    # combine terms
    product = xuv_time_shifted * p_A_int_mat * e_fft

    # integrate
    integral = product.sum(axis=2)

    return np.abs(integral)**2

















    exit(0)













N = 2**15
xuv = XUV_Field(N=N, tmax=60e-15)
ir = IR_Field(N=N, tmax=60e-15)
med = Med()


# fig, ax = plt.subplots(1, 1)
# ax.plot(xuv.tmat, np.real(xuv.Et), color='blue')
# axtwin = ax.twinx()
# axtwin.plot(ir.tmat, ir.Et, color='orange')
#
#
# fig2, ax2 = plt.subplots(1, 1)
# ax2.plot(xuv.tmat, np.real(xuv.Et), color='blue')
# axtwin = ax2.twinx()
# axtwin.plot(ir.tmat, ir.Et, color='orange')
# ax2.set_xlim(-8, 8)

# construct delay axis
N = ir.N
df = 1 / (ir.dt * N)
dt = ir.dt
fvec = df * np.arange(-N/2, N/2, 1)

# frequency and time vectors
frequency_positive = fvec[int(len(fvec)/2):]
p_vec = np.sqrt(2 * frequency_positive)

tvec =  ir.tmat
tauvec = tvec[:]

# calculate At
A_t = -1 * dt * np.cumsum(ir.Et)
A_t_integ = -1 * np.flip(dt * np.cumsum(np.flip(A_t)))
items = {'A_t_integ': A_t_integ, 'Exuv': xuv.Et, 'Ip': med.Ip}


print(np.shape(tauvec))
print(np.shape(p_vec))
print(len(tauvec)/512)
print(len(p_vec)/512)


split = 512
image = np.zeros((512, 512))

# index_im = (0, 0)
# index_alg = (0:32, 0:64)

# index_im = (0, 1)
# index_alg = (0:32, 65:128)



integral = calculate(tau_slice=tauvec[0:64], p_slice=p_vec[0:32],
          time=tvec, frequency_whole=fvec, items=items)

point = np.average(integral)


plt.show()



exit(0)