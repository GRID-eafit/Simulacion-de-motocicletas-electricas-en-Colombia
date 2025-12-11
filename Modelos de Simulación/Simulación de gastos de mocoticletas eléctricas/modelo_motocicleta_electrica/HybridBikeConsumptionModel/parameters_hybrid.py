class HEV:
    def __init__(self):
        self.EM = EM()
        self.Buck = Buck()
        self.Battery = Battery()
        self.Engine = Engine()
        self.Carburator = Carburator()
        self.Chassis = Chassis()
        self.Wheel = Wheel()
        self.Brake = Brake()
        self.Chain = Chain()
        self.Trans = Trans()
        self.Ambient = Ambient()


# Class electric Motor
class EM:
    kit = 7.6      # Armature coefficient t []
    kiw = 6       # Armature coefficient w []
    ra = 1/0.0345   # Inductor armature
    la = 1/850e-6   # Inductor armature


# Class Buck converter
class Buck:
    ub = 74
    lp = 0.05
    cp = 110e-3
    rp = 1


# Class Battery
class Battery:
    uoc = 74        # Open circuit voltage [V]
    ro = 1.65/1000  # Resistive cell [Ohm]
    r_1 = 0.165
    c_1 = 43.8
    r_0 = 0.108
    n = 1   # Coulomb efficiency (assume ideal)
    q = 25  # Capacity [Ah]


# Class Engine
class Engine:
    je = 0.35                   # Power train moment inertia [Kg-m2]
    f_sft = 0.015               # Viscous friction coefficient [N-m-s/rad]
    hu = 85                     # Fuel energy const[J / kg]
    nu = 0.8                    # Thermal efficiency[ %]
    neutraload = 0              # Load torque in neutra [N.m]
    vd = 125                    # Engine displacement volume [cm ^ 3]
    wice_min = 1000/9.5493      # Engine minimum speed[rad / seg]
    wice_max = 20000/9.5493     # Engine maximum speed[rad / seg]


# Class Carburator
class Carburator:
    tind_ralenti = Engine().neutraload + Engine().f_sft * Engine().wice_min
    tind_rpmMax = Engine().neutraload + Engine.f_sft * Engine().wice_max
    mf_min = tind_ralenti * Engine().wice_min / (Engine().hu * Engine().nu)
    mf_max = tind_rpmMax * Engine().wice_max / (Engine().hu * Engine().nu)
    m = 1/(mf_max - mf_min)  # Slope equation


# Class Chassis
class Chassis:
    m = 200     # Vehicle mass [kg]
    a = 0.6     # Frontal area [m²]
    cd = 0.7    # Drag coefficient [-]

    crr = 0.01  # Rolling coefficient[-]


# Class Wheel
class Wheel:
    rw = 0.2667     # Wheel radius [m]
    jw = 0          # Wheel moment of inertia[kg - m²]


# Class Brake
class Brake:
    cn = -1000      # Brake force constant[N]


# Class Chain
class Chain:
    input = 15             # input gear chain teeth
    output = 38            # Output gear chain sproket teeth
    rc = output/input      # Secondary transmition gear ratio


# Class Transmission
class Trans:
    # Ratio --- Output/input -- speed
    # Gear number of teeths from output shaft
    s1 = 36
    s2 = 32
    s3 = 28
    s4 = 26
    s5 = 24
    # Gear number of teeths from input clutch shaft
    c1 = 12
    c2 = 17
    c3 = 20
    c4 = 23
    c5 = 25

    # Primary transmition march Gear ratio
    r1 = c1 / s1
    r2 = c2 / s2
    r3 = c3 / s3
    r4 = c4 / s4
    r5 = c5 / s5

    # Gear ratio
    gear_1 = 3.08333
    gear_2 = 1.882352941
    gear_3 = 1.4
    gear_4 = 1.130434783
    gear_5 = 0.96

    # Gear ratio Final
    gear_1final = r1 / Chain().rc
    gear_2final = r2 / Chain().rc
    gear_3final = r3 / Chain().rc
    gear_4final = r4 / Chain().rc
    gear_5final = r5 / Chain().rc


# Class Ambiental
class Ambient:
    g = 9.8     # Gravity constant [m/s²]
    rho = 1.21  # Air Density [Kg/m³]
