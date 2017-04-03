# Script to generate the walker beam equations
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from sympy import *

################################################################################
#                              Symbol Definitions                              #
################################################################################

x0, xp0, p1hx, p1hz, m1hx, m1hz, a1, p2hx, p2hz, m2hx, m2hz, a2, p3hx, p3hz, dg3x, dg3z = symbols(
    "x0 xp0 p1hx p2hz m1hx m1hz a1 p2hx p2hz m2hx m2hz a2 p3hx p3hz dg3x dg3z")
p1hxp, p2hxp, p3hxp, dg3xp = symbols("p1hxp p2hxp p3hxp dg3xp")
m1hxp, m2hxp = symbols("m1hxp m2hxp")
m1hdx, m2hdx = symbols("m1hdx m2hdx")
d1, d2, d3, d4, d5, d6 = symbols("d1 d2 d3 d4 d5 d6")

# The beam at any point in the beamline needs an x, z, and xp to be fully
# characterized.

# import ipdb; ipdb.set_trace()

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
x, z = symbols("x z")
# Using point slope eq for a line to get line of M1H (point is d2, m1hdx)
m1h_ln = a1 * (z - d2) + m1hdx - x
# Solve for x
m1h_ln_x = solve(m1h_ln, x)[0]
# Get the line eq for the beam
beam_ln = x0 + z * xp0
# Setting them equal to each other and subtracting, then solving for z
m1hz = solve(m1h_ln_x - beam_ln, z)[0]
# Plugging this z into the eq for the beam line to get x point of intersection
m1hx = simplify(x0 + m1hz * xp0)
# Define the new angle of reflection
m1hxp = 2*a1 - xp0


print("\nM1H X: {0}".format(m1hx))
print("M1H Z: {0}".format(m1hz))
print("M1H XP: {0}".format(m1hxp))

################################################################################
#                                     P2H                                      #
################################################################################

p2hz = d3
# X position follows the line eq but using x position at m1h and new angle
p2hx_eq = m1hx + m1hxp * (d3-m1hz)
# Simplify
p2hx = simplify(p2hx_eq)
# Angle of the beam isnt changing
p2hxp = m1hxp

# For walker, we need to be able to get an alpha for a desired x position
# Declare generic x
# x = symbols("x")
# # Solve p1h x for alpha
# p2h_alpha = simplify(solve(p2hx - x, a1))

print("\nP2H X: {0}".format(p2hx))
print("P2H Z: {0}".format(p2hz))
print("P2H XP: {0}".format(p2hxp))

################################################################################
#                                     M2H                                      #
################################################################################

# Declare generic x and z
x, z = symbols("x z")
# Using point slope eq for a line to get line of M1H (point is d4, m2hdx)
m2h_ln = a2 * (z - d4) + m2hdx - x
# Solve for x
m2h_ln_x = solve(m2h_ln, x)[0]
# Get the line eq for the beam using beam parameters from m1h in point slope
beam_ln =  m1hxp*(z - m1hz) + m1hx - x
# Solve for x
beam_ln_x = solve(beam_ln, x)[0]
# Setting them equal to each other and subtracting, then solving for z
m2hz = solve(m2h_ln_x - beam_ln_x, z)[0]
# Plugging this z into the eq for the beam line to get x point of intersection
m2h_sub = beam_ln.subs(z, m2hz)
# Solve for x
m2hx = solve(m2h_sub, x)[0]
# Reflection angle
m2hxp = 2*a2 - m1hxp

# x, z = symbols("x z")
# m2hx_x_subs = m2hx.subs(m2hdx, x) - x
# print(m2hx_x_subs)
# m2hx_x = solve(m2hx_x_subs, x)
# print(m2hx_x)


print("\nM2H X: {0}".format(m2hx))
print("M2H Z: {0}".format(m2hz))
print("M2H XP: {0}".format(m2hxp))

################################################################################
#                                     P3H                                      #
################################################################################

p3hz = d5
# X position follows the line eq but using x position at m2h and new angle
p3hx_eq = m2hx + m2hxp*(d5-m2hz)
# Simplify
p3hx = simplify(p3hx_eq)
# Angle doesn't change
p3hxp = m2hxp

# For walker, we need to be able to get an alpha 1 for a desired x position
# Declare generic x
x = symbols("x")
# Solve p1h x for alpha
p3h_alpha = solve(p3hx - x, a1)[0]

# print(p3h_alpha)


print("\nP3H X: {0}".format(p3hx))
print("P3H Z: {0}".format(p3hz))
print("P3H XP: {0}".format(p3hxp))
print("Alpha1: {0}".format(p3h_alpha))

################################################################################
#                                     DG3                                      #
################################################################################

dg3z = d6
# X position follows the line eq but using x position at m2h and new angle
dg3x_eq = m2hx + m2hxp*(d6-m2hz)
# Simplify
dg3x = simplify(dg3x_eq)
# Angle doesn't change
dg3xp = m2hxp

# For walker, we need to be able to get an alpha 1 for a desired x position
# Declare generic x
x = symbols("x")
# Solve p1h x for alpha
dg3_alpha = solve(dg3x - x, a2)[0]

# print(dg3_alpha)

print("\nDG3 X: {0}".format(dg3x))
print("DG3 Z: {0}".format(dg3z))
print("DG3 XP: {0}".format(dg3xp))
print("Alpha2: {0}".format(dg3_alpha))


################################################################################
#                              Analytical Solution                             #
################################################################################



# Substitute the second equation into alpha_2 in the first
alpha_1_eq = p3h_alpha.subs(a2, dg3_alpha)

# Move alpha_1 over to the right and re-solve for alpha_1 with the substitutions
alpha_1 = solve(alpha_1_eq - a1, a1)

# print(alpha_1_eq)
print(alpha_1)
