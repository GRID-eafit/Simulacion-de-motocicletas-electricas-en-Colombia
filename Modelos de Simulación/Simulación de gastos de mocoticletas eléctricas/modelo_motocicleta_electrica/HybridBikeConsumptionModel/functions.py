def RK(tsim, dt, x0, delta, hybrid_cont, last_vel):
    import numpy as np

    xi = np.zeros((len(x0), 1))
    h = dt
    tsim_1 = tsim - dt

    k_1 = model(tsim_1, x0, delta, hybrid_cont, last_vel, dt)
    k_2 = model(tsim_1 + 0.5 * h, x0 + 0.5 * h * k_1, delta, hybrid_cont, last_vel, dt)
    k_3 = model(tsim_1 + 0.5 * h, x0 + 0.5 * h * k_2, delta, hybrid_cont, last_vel, dt)
    k_4 = model(tsim_1 + h, x0 + k_3 * h, delta, hybrid_cont, last_vel, dt)

    xi = x0 + (1 / 6) * (k_1 + 2 * k_2 + 2 * k_3 + k_4) * h  # main equation

    x = xi

    return x


def model(t, x, u, hybrid_cont, last_vel, dt):
    if hybrid_cont == 0:
        from HybridBikeConsumptionModel.parameters_electric import HEV
    else:
        from HybridBikeConsumptionModel.parameters_hybrid import HEV
    import numpy as np
    # State and Control Vectors

    # States
    vhev = x[0]  # Velocity state [m/s]
    iind = x[2]  # Inductor current [A]
    im = x[3]  # Motor current [A]
    um = x[4]  # Motor voltage [V]
    wice = x[6]  # Engine angular velocity [rad/seg]
    i_r1 = x[7]  # Batery thevennin current [A]

    # Inputs
    alpha_t = u[0]  # Throttle control [%, 0-1] ****
    delta_t = u[2]  # Duty cycle [%, 0-1]       ****
    gamma = u[1]  # Shift gear []
    theta = u[3]  # road inclination [rad]
    beta_t = u[4]  # Clutch command, Slipping or locked
    brake = u[5]  # Brake force for perturbation

    # Load parameters
    hev = HEV()

    # Gear hybrid model
    if gamma == 1:
        gear = hev.Trans.r1 * hev.Chain.rc
    elif gamma == 2:
        gear = hev.Trans.r2 * hev.Chain.rc
    elif gamma == 3:
        gear = hev.Trans.r3 * hev.Chain.rc
    elif gamma == 4:
        gear = hev.Trans.r4 * hev.Chain.rc
    elif gamma == 5:
        gear = hev.Trans.r5 * hev.Chain.rc
    else:
        gear = hev.Trans.r1 * hev.Chain.rc

    # Wheel angular velocity
    ww = vhev / hev.Wheel.rw    # Wheel angular velocity [rad/s]
    wem = ww                    # Electric motor angular velocity [rad/s]

    # Electric motor
    ui = wem * hev.EM.kiw  # induced voltage back emf [V]

    # Enviroment forces
    # Velocidad viento
    vw = 0
    vhev = vw + vhev

    # Aerodynamic force
    faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vhev ** 2)
    # Rolling force
    froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * np.cos(theta) #* vhev # duda, no sabemos si rodadura aumenta con la vel
    # Gravity force
    fg = hev.Ambient.g * hev.Chassis.m * np.sin(theta)
    # Pertubation force
    fdist = 0

    #Inertia

    delta_v = vhev - last_vel
    f_inertia = hev.Chassis.m * delta_v/dt
    # Sum Forces
    fres = faero + froll + fg + fdist + f_inertia

    # calculos Mauro
    p_e = vhev * fres
    p_m = (fres * hev.Wheel.rw) * (vhev / hev.Wheel.rw)# * (1 - hybrid_cont)
    #print(p_e, p_m)
    #if abs(delta_v) < 1:
    #print(p_m, p_e)
    p_eb = p_m * (1 - hybrid_cont)/ 0.7
    #else:
    #p_eb = p_e / (p_m * 0.7)  # 0.7 es la eficiencia (estimada) del tren motriz

    # Electric
    # Battery
    # Input current
    ib = im * delta_t  # Battery load [A]

    # Open circuit voltage (OCV)
    ocv = 74

    # Kirchoff - sum of voltage
    ub = ocv - hev.Battery.r_1 * i_r1 - hev.Battery.r_0 * ib  # Terminal voltage [V]

    # Derivatives
    i_r1_dot = - (1 / (hev.Battery.r_1 * hev.Battery.c_1)) * i_r1 + (1 / (hev.Battery.r_1 * hev.Battery.c_1)) * ib
    #soc_dot = -hev.Battery.n * im * abs(delta_t) / (hev.Battery.q * 3600) # SOC [%]
    soc_dot = -hev.Battery.n * im * abs(delta_t) / (hev.Battery.q * 3600)  # SOC [%]

    # Buck Converter
    im_dot = -um / hev.Buck.lp + (ub / hev.Buck.lp) * delta_t
    um_dot = (im / hev.Buck.cp) - um / (hev.Buck.cp * hev.Buck.rp)

    # Armature inductor
    iind_dot = (um - hev.EM.ra * iind - ui) / hev.EM.la  # Current flow trow inductor armature [A]

    # Electric motor
    tem = im * hev.EM.kit  # Torque electric motor [N_m]

    # Combustion
    # Carburator
    # air mass flow rate [kg/sec]
    mbeta_dot = hev.Carburator.mf_min
    # Fuel mass flow rate [kg/sec]
    malpha_dot = alpha_t * (1/hev.Carburator.m)

    # Fuel-air mass flow rate [kg/sec]
    mf_dot = mbeta_dot + malpha_dot

    # Engine
    # Engine Combustion Torque [N-m] in flywheel
    if wice == 0:
        tice_comb = 0
    else:
        tice_comb = hev.Engine.hu * hev.Engine.nu * mf_dot / wice

    # Engine load torque in the wheel
    tload = fres * hev.Wheel.rw

    # Brake couple
    if vhev < 0:
        fbrake = 0
    else:
        fbrake = brake * hev.Brake.cn  # Brake force

    # Mechanical Dynamics
    # Total torque in the flywheel
    if beta_t == 0:
        ttot = tice_comb - hev.Engine.f_sft * wice
    else:  # Clutch locked
        ttot = tice_comb + (1/gear)*tem - (1/gear)*tload - hev.Engine.f_sft*wice + (1/gear)*fbrake*hev.Wheel.rw

    # MEngine dynamic velocity rotation
    wice_dot = (1/hev.Engine.je)*ttot

    # Torque to forces in the body

    # Engine force
    fice = (tice_comb - hev.Engine.f_sft*wice)*gear/hev.Wheel.rw

    # Motor Force
    fem = tem/hev.Wheel.rw

    # Sumatory of forces in the wheel
    if beta_t == 0:
        ftot = fem + fbrake - fres
    else:
        ftot = fice + fem + fbrake - fres

    # Mass of the vehicle
    mhev = hev.Chassis.m + hev.Engine.je*(gear**2 / hev.Wheel.rw**2)

    # Traslational dynamics and kinematics
    # Dynamics
    vhev_dot = ftot / mhev
    # Kinematics
    phev_dot = vhev

    # Derivative Vector
    xdot = np.array([vhev_dot, phev_dot, iind_dot, im_dot, um_dot, soc_dot, wice_dot, i_r1_dot, p_eb]).T

    return xdot


def wmtc_profile(ts, tini, tfin, v):
    import numpy as np
    time = np.arange(0, len(v), 1, dtype=int)
    vq = np.arange(tini, tfin, ts)
    v_profile = np.interp(vq, time, v)

    return v_profile

