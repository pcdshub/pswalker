# Script to generate the walker beam equations

# For a full explanation see the jupyter notebook named "Ray Tracing for Tilted
# Flat Mirrors" in the "ipynbs" directory

from __future__ import absolute_import, division, print_function

import sympy as sp

################################################################################
#                              Symbol Definitions                              #
################################################################################

x0, xp0 = sp.symbols("x0 xp0")                    # Source beam x pointing
p1hx, p1hz, p1hxp = sp.symbols("p1hx p2hz p1hxp")   # P1H beam x,z, pointing
m1hx, m1hz, a1 = sp.symbols("m1hx m1hz a1")       # M1H beam x,z, mirror angle
p2hx, p2hz, p2hxp = sp.symbols("p2hx p2hz p2hxp")   # P2H beam x,z, pointing
m2hx, m2hz, a2 = sp.symbols("m2hx m2hz a2")       # M2H beam x,z, mirror angle
p3hx, p3hz, p3hxp = sp.symbols("p3hx p3hz p3hxp")   # P3H beam x,z, pointing
dg3x, dg3z, dg3xp = sp.symbols("dg3x dg3z dg3xp")   # DG3 beam x,z, pointing
m1hxp, m2hxp = sp.symbols("m1hxp m2hxp")            # Pointing after mirror
m1hdx, m2hdx = sp.symbols("m1hdx m2hdx")                   # X position of mirror
d1, d2, d3, d4, d5, d6 = sp.symbols("d1 d2 d3 d4 d5 d6")   # Z positions

################################################################################
#                                     P1H                                      #
################################################################################

p1hx = x0 + d1 * xp0
p1hz = d1
p1hxp = xp0

################################################################################
#                                     M1H                                      #
################################################################################

# Declare generic x and z
x, z = sp.symbols("x z")
# Using point slope eq for a line to get line of M1H (point is d2, m1hdx)
m1h_ln = a1 * (z - d2) + m1hdx - x
# Solve for x
m1h_ln_x = sp.solve(m1h_ln, x)[0]
# Get the line eq for the beam
beam_ln = x0 + z * xp0
# Setting them equal to each other and subtracting, then solving for z
m1hz = sp.solve(m1h_ln_x - beam_ln, z)[0]
# Plugging this z into the eq for the beam line to get x point of intersection
m1hx = sp.simplify(x0 + m1hz * xp0)
# Define the new angle of reflection
m1hxp = 2*a1 - xp0

print("\nM1H X: {0}".format(m1hx))
print("M1H Z: {0}".format(m1hz))
print("M1H XP: {0}".format(m1hxp))

# Output:
# M1H X: (a1*d2*xp0 + a1*x0 - m1hdx*xp0)/(a1 - xp0)
# M1H Z: (a1*d2 - m1hdx + x0)/(a1 - xp0)
# M1H XP: 2*a1 - xp0

################################################################################
#                                     P2H                                      #
################################################################################

p2hz = d3
# X position follows the line eq but using x position at m1h and new angle
p2hx_eq = m1hx + m1hxp * (d3-m1hz)
# Simplify
p2hx = sp.simplify(p2hx_eq)
# Angle of the beam isnt changing
p2hxp = m1hxp

print("\nP2H X: {0}".format(p2hx))
print("P2H Z: {0}".format(p2hz))
print("P2H XP: {0}".format(p2hxp))

# Output:
# P2H X: -2*a1*d2 + 2*a1*d3 - d3*xp0 + 2*m1hdx - x0
# P2H Z: d3
# P2H XP: 2*a1 - xp0

################################################################################
#                                     M2H                                      #
################################################################################

# Declare generic x and z
x, z = sp.symbols("x z")
# Using point slope eq for a line to get line of M1H (point is d4, m2hdx)
m2h_ln = a2 * (z - d4) + m2hdx - x
# Solve for x
m2h_ln_x = sp.solve(m2h_ln, x)[0]
# Get the line eq for the beam using beam parameters from m1h in point slope
beam_ln = m1hxp*(z - m1hz) + m1hx - x
# Solve for x
beam_ln_x = sp.solve(beam_ln, x)[0]
# Setting them equal to each other and subtracting, then solving for z
m2hz = sp.solve(m2h_ln_x - beam_ln_x, z)[0]
# Plugging this z into the eq for the beam line to get x point of intersection
m2h_sub = beam_ln.subs(z, m2hz)
# Solve for x
m2hx = sp.solve(m2h_sub, x)[0]
# Reflection angle
m2hxp = 2*a2 - m1hxp

print("\nM2H X: {0}".format(m2hx))
print("M2H Z: {0}".format(m2hz))
print("M2H XP: {0}".format(m2hxp))

# Output:
# M2H X: (2*a1*a2*d2 - 2*a1*a2*d4 + 2*a1*m2hdx + a2*d4*xp0 - 2*a2*m1hdx + a2*x0 - m2hdx*xp0)/(2*a1 - a2 - xp0)
# M2H Z: (-2*a1*d2 + a2*d4 + 2*m1hdx - m2hdx - x0)/(-2*a1 + a2 + xp0)
# M2H XP: -2*a1 + 2*a2 + xp0

################################################################################
#                                     P3H                                      #
################################################################################

p3hz = d5
# X position follows the line eq but using x position at m2h and new angle
p3hx_eq = m2hx + m2hxp*(d5-m2hz)
# Simplify
p3hx = sp.simplify(p3hx_eq)
# Angle doesn't change
p3hxp = m2hxp

# For walker, we need to be able to get an alpha 1 for a desired x position
# Declare generic x
xp3h = sp.symbols("xp3h")
# Solve p1h x for alpha
p3h_alpha = sp.solve(p3hx - xp3h, a1)[0]

print("\nP3H X: {0}".format(p3hx))
print("P3H Z: {0}".format(p3hz))
print("P3H XP: {0}".format(p3hxp))
print("Alpha1: {0}".format(p3h_alpha))

# Output:
# P3H X: 2*a1*d2 - 2*a1*d5 - 2*a2*d4 + 2*a2*d5 + d5*xp0 - 2*m1hdx + 2*m2hdx + x0
# P3H Z: d5
# P3H XP: -2*a1 + 2*a2 + xp0
# Alpha1: (a2*d4 - a2*d5 - d5*xp0/2 + m1hdx - m2hdx - x0/2 + xp3h/2)/(d2 - d5)

################################################################################
#                                     DG3                                      #
################################################################################

dg3z = d6
# X position follows the line eq but using x position at m2h and new angle
dg3x_eq = m2hx + m2hxp*(d6-m2hz)
# Simplify
dg3x = sp.simplify(dg3x_eq)
# Angle doesn't change
dg3xp = m2hxp

# For walker, we need to be able to get an alpha 1 for a desired x position
# Declare generic x
xdg3 = sp.symbols("xdg3")
# Solve p1h x for alpha
dg3_alpha = sp.solve(dg3x - xdg3, a2)[0]

print("\nDG3 X: {0}".format(dg3x))
print("DG3 Z: {0}".format(dg3z))
print("DG3 XP: {0}".format(dg3xp))
print("Alpha2: {0}".format(dg3_alpha))

# Output:
# DG3 X: 2*a1*d2 - 2*a1*d6 - 2*a2*d4 + 2*a2*d6 + d6*xp0 - 2*m1hdx + 2*m2hdx + x0
# DG3 Z: d6
# DG3 XP: -2*a1 + 2*a2 + xp0
# Alpha2: (a1*d2 - a1*d6 + d6*xp0/2 - m1hdx + m2hdx + x0/2 - xdg3/2)/(d4 - d6)

################################################################################
#                              Analytical Solution                             #
################################################################################

# Substitute the second equation into alpha_2 in the first
alpha_1_eq = p3h_alpha.subs(a2, dg3_alpha)

# Move alpha_1 over to the right and re-solve for alpha_1 with the substitutions
alpha_1 = sp.solve(alpha_1_eq - a1, a1)[0]

print("\nAlpha1: {0}".format(alpha_1))

# Outputs:
# Alpha1: (-d4*d5*xp0 + d4*d6*xp0 - d4*xdg3 + d4*xp3h + 2*d5*m1hdx - 2*d5*m2hdx - d5*x0 + d5*xdg3 - 2*d6*m1hdx + 2*d6*m2hdx + d6*x0 - d6*xp3h)/(2*(d2*d5 - d2*d6 - d4*d5 + d4*d6))
