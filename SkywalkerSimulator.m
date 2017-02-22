function varargout = SkywalkerSimulator(varargin)
% SkywalkerSimulator M-file for SkywalkerSimulator.fig
%      SkywalkerSimulator, by itself, creates a new SkywalkerSimulator or raises the existing
%      singleton*.
%
%      H = SkywalkerSimulator returns the handle to a new SkywalkerSimulator or the handle to
%      the existing singleton*.
%
%      SkywalkerSimulator('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in SkywalkerSimulator.M with the given input arguments.
%
%      SkywalkerSimulator('Property','Value',...) creates a new SkywalkerSimulator or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before SkywalkerSimulator_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to SkywalkerSimulator_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help SkywalkerSimulator

% Last Modified by GUIDE v2.5 13-Feb-2017 14:39:40

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @SkywalkerSimulator_OpeningFcn, ...
                   'gui_OutputFcn',  @SkywalkerSimulator_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before SkywalkerSimulator is made visible.
function SkywalkerSimulator_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to SkywalkerSimulator (see VARARGIN)

% Choose default command line output for SkywalkerSimulator
handles.output = hObject;
set(handles.table,'rowname',{'photon_en','FEE_slit_x','FEE_slit_y','XGA','YGA','X0','X0P','X1','X1P','X2','X2P','aptX','aptY','ang','LHOMS','Y0','Y0P'})
data{1,1}=5000;
data{2,1}=3E-3;
data{3,1}=3e-3;
data{4,1}=0;
data{5,1}=0;
data{6,1}=0;
data{7,1}=0;
data{8,1}=0;
data{9,1}=0;
data{10,1}=0;
data{11,1}=0;
data{12,1}=5.5e-3;
data{13,1}=0;
data{14,1}=0;
data{15,1}=0.45;
data{16,1}=0;
data{17,1}=0;
set(handles.edit1,'string','501')
set(handles.edit2,'string','501')
set(handles.table,'data',data);




% Update handles structure
guidata(hObject, handles);

% UIWAIT makes SkywalkerSimulator wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = SkywalkerSimulator_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;



function edit1_Callback(hObject, eventdata, handles)
% hObject    handle to edit1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit1 as text
%        str2double(get(hObject,'String')) returns contents of edit1 as a double


% --- Executes during object creation, after setting all properties.
function edit1_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
%'rowname',{'photon_en','FEE_slitx','FEEslity','XGA','YGA','X0','X0P','X1','X1P','X2','X2P','aptX','aptY','ang','LHOMS',Y0,'Y0P})
% --- Executes on button press in Start.
function Start_Callback(hObject, eventdata, handles)
parameter=get(handles.edit1,'string');
disp(parameter)
parameter2=get(handles.edit2,'string');
disp(parameter2);
Mx=str2num(parameter)
My=str2num(parameter2)
tabled = get(handles.table,'data');
display(tabled)
photon_en=tabled{1}
FEE_Slit_x=tabled{2}
FEE_Slit_y=tabled{3}
XGA=tabled{4}
YGA=tabled{5}
X0=tabled{6}
X0P=tabled{7}
X1=tabled{8}
X1P=tabled{9}
X2=tabled{10}
X2P=tabled{11}
aptX=tabled{12}
aptY=tabled{13}
ang=tabled{14}
LHOMS=tabled{15}
Y0=tabled{16}
Y0P=tabled{17}
DataRead=get(handles.table,'data')
handles.DataRead=DataRead;
handles.Mx=Mx;
handles.My=My;
guidata(hObject, handles);
SimTraceProp;
plot(handles.axes1,x/convr,Isn(:,Ty),'r-')
hold(handles.axes1,'on')
plot(handles.axes1,y/convr,Isn(Tx,:),'-')
axis(handles.axes1,[-inf inf 0 inf]) 
hold(handles.axes1,'off')
plot(handles.axes2,y/convr,IDG3(:,Ty),'-')
axis(handles.axes2,[-2e-3 2e-3 0 inf]) 
hold(handles.axes2,'off')
% ESfr,x_out_f,y_out_f,Txx,Tyy
imagesc(y/convr,x/convr,Isn'/max(max(Isn)),'parent',handles.axes4)
axis(handles.axes4,[-2e-3 2e-3 -2e-3 2e-3]) 
title(handles.axes4,'P2H')
% set(handles.axes4,'YDir','reverse')
set(handles.axes4,'YDir','normal')
imagesc(y/convr,x/convr,IDG3'/max(max(IDG3)),'parent',handles.axes5)
axis(handles.axes5,[-4e-3 4e-3 -4e-3 4e-3]) 
title(handles.axes5,'DG3')
set(handles.axes5,'YDir','normal')
imagesc(y/convr,x/convr,IP3H'/max(max(IP3H)),'parent',handles.axes6)
axis(handles.axes6,[-2e-3 2e-3 -2e-3 2e-3]) 
title(handles.axes6,'P3H')
set(handles.axes6,'YDir','normal')
handles.IDG3=IDG3;
guidata(hObject, handles);

% % --- Executes on button press in debug.
% function debug_Callback(hObject, eventdata, handles)
% figure(100)
% imagesc((abs(handles.ESLfr).^2/max(max(abs(handles.ESLfr))).^2))
% axis([-5e-4 5e-4 -5e-4 +5e-4])

function edit2_Callback(hObject, eventdata, handles)
% hObject    handle to edit2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit2 as text
%        str2double(get(hObject,'String')) returns contents of edit2 as a double


% --- Executes during object creation, after setting all properties.
function edit2_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


% --- Executes on button press in pushbutton4.
function pushbutton4_Callback(hObject, eventdata, handles)
% hObject    handle to pushbutton4 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
