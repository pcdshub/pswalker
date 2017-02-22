function [out_wf,dxs_out,dys_out] = f_2D_lens_prop_spectr_jac_fx_fy_shift(dx,dy,Z,Rdx,Rdy,fx,fy,ut0)
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



z_prim_x = (1/Rdx + 1/Z - 1/fx)^-1; % "effective" propagation distance z_prim_x

z_prim_y = (1/Rdy + 1/Z - 1/fy)^-1; % "effective" propagation distance z_prim_y
Z_bis = sqrt(z_prim_x*z_prim_y);  % geometric average


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
r_sqr=(X).^2/Rdx+(Y).^2/Rdy;


%======================
% FFT of the input field  with spherical part removed 
% and a shift  - moving the zero-frequency component to the center of the array
%======================


fwf0 = fftshift(fft2(ifftshift(ut0.*exp(1i/2.*(-r_sqr)))));
%===========================


%===================================
% calculating the product of square of  k-vector components
% times "effective" propagation distances z_prim_x and z_prim_y


kx = dkx*((1:Mx)-Tx); ky = dky*((1:My)-Ty); 
[KY,KX] = meshgrid(ky,kx);
k_sqr=(KX).^2*z_prim_x+(KY).^2*z_prim_y;

swe='second';
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

%out_wf_prim = ph_p.*(ifft2(wf_prop.*ph_p)); % output function derived from "flatened" input field  
out_wf_prim = fftshift((ifft2(ifftshift(wf_prop))));
%===================================

% Finally  the output field 
%==================================
out_wf = zeros(Mx,My);
swe='third';

for ii=1:Mx         
    for jj = 1:My

        out_wf(ii,jj)= out_wf_prim(ii,jj)*(Z_bis/Z)*exp(1i/2*(((x(ii))^2)*(Z-z_prim_x)/(z_prim_x)^2 +((y(jj)^2)*(Z-z_prim_y)/(z_prim_y)^2)));    % w_sqr=s freq square matrix
       
    end
end

%===================================
% and the otput metrics 
%==================================
dxs_out = Z/z_prim_x*dx; 
dys_out = Z/z_prim_y*dy; 