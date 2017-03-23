function [ xi,zi,vrefl,xis,zis ] = JacRaytrace( nrx,nrz,xr,zr,nmx,nmz,xm,zm,nsx,nsz,xs,zs)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here


[ xi,zi,vrefl ] = JacSec( nrx,nrz,xr,zr,nmx,nmz,xm,zm);
[ xis,zis ] = JacSec( vrefl(1),vrefl(2),xi,zi,nsx,nsz,xs,zs);



end

