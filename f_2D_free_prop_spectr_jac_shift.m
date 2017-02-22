function [out_wf] = f_2D_free_prop_spectr_jac_shift(dx,dy,Z,ut0)
%  Spectral/Fourier Wavefront  Propagation Algorithm
% ==Inputs==
% ut0 = Input field in the space domain
% dx, dy space steps of the ut0 matrix
% Z = propagation distance
% Rd radius of the curvature of the input field
% f focal length
% phase_errors
% ==Outputs==

%out_wf = Output field in space domain
% written by Jacek Krzywinski

%=============================================================
% Propagation , 0 to Z
%=============================================================

[Mx,My] = size(ut0);
Tx=(Mx+1)/2; Ty= (My+1)/2;

%============================
%k-vector steps
%============================

dkx = 2*pi/(Mx*dx);
dky = 2*pi/(My*dy);


%=============================================
%  x and y  vectors and r_sqr = x^2 + y^2  matrix
%=============================================

x = dx*((1:Mx)-Tx); y = dy*((1:My)-Ty); 
[Y,X] = meshgrid(y,x);
r_sqr=(X).^2+(Y).^2;


%======================
% FFT of the input field  with spherical part removed 
% and a shift  - moving the zero-frequency component to the center of the array
%======================
fwf0 = fftshift(fft2(ifftshift(ut0)));
%===========================
%===================================
% calculating the product of square of  k-vector components
% times "effective" propagation distances z_prim_x and z_prim_y


kx = dkx*((1:Mx)-Tx); ky = dky*((1:My)-Ty); 
[KY,KX] = meshgrid(ky,kx);

k_sqr=((KX).^2+(KY).^2)*Z;

%===================================
% Propagator 
%==================================

Dh = exp((-1i/2).*k_sqr);


%===================================
% Propagator * shifted Fourier transform of the "flat" input field
%==================================
wf_prop = Dh.*fwf0;

%===================================
% Shifted Inverse Fourier transform 
%  moving the zero-frequency component to the center of the array-> Output field
%==================================
%===================================
% the output field 
%==================================

out_wf = fftshift((ifft2(ifftshift(wf_prop))));

