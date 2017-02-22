function [ xi,zi,vrefl ] = JacSec( nrx,nrz,xr,zr,nmx,nmz,xm,zm)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

A=[nrx -nrz;nmx -nmz];
b=[nrx*xr-nrz*zr;nmx*xm-nmz*zm];
x=A\b;

xi=x(1);  zi=x(2);

vr=[nrx nrz];
vm=[nmx nmz];
U1=vertcat(vr,vm);
phir=acos(dot(vr,vm))*sign(det(U1));

vIr=nrx+1i*nrz;
vIrefl=exp(1i*2*phir)*vIr;
vrefl=[real(vIrefl) imag(vIrefl)];

end

