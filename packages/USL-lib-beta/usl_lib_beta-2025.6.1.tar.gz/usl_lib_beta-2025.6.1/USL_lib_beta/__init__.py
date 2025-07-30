#!/usr/bin/env python
# coding: utf-8

## 超稳激光系统用到的主要的函数集合，整合了ad、psd、线漂补偿、三角帽计算
## 作者：zxq

## Update Time：20241024
## change log: 添加控温层温度读取函数，绘制控温层温度随时间变化，PSD，adev曲线

## Update Time：20241022
## change log: 修改adev，mdev,hdev,oadev函数输入参数，修改三角帽计算adev函数，添加fs=50Hz和100Hz在1s处取点

## Update Time：20240901
## change log: 修改画图比例，图例，字体大小等，

## Update Time：20240101
## change log: plot_keysight_USB_power, plot_pico_USB_err

## Update Time：20231023
## change log: ad function pn_plot_to_psd, oscilloscope_data_read

## Update Time：20231009
## change log: ad function K_K_plot

## 更新时间：2023/07/07

## 新增psd_welch函数，使用welch函数，绘制PSD（与plt.psd略有不同）
## 新增psd_int_allan函数，从频域起点开始积分计算对allan方差秒稳的影响

## 更新时间：2022/04/27
## 新增CSD(cross power spectral density)函数绘制
## KK_data_read函数增加起始终止参数,增加输出参数
## 补长漂，新增开关参数
## psd函数添加标签参数

## 更新时间：2022/04/25
## 新增labview自编程序数据读取

## 更新时间：2022/06/29
## 新增sr780数据读取以及拼接后算allan deviation


# import packages
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mpl_toolkits.axisartist as axisartist
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
from pdf2image import convert_from_path
import scipy.linalg as linalg
import scienceplots
import time
from datetime import datetime
from cProfile import label
import allantools as alt
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
import time
from scipy import optimize,signal
from datetime import datetime, date, timedelta
from pathlib import Path
from scipy import special
import matplotlib.path as mpath
from scipy.fftpack import fft

# # from ultra_stable_laser_python_library import *

# # %matplotlib inline
# # %config InlineBackend.figure_format='retina'

# Define colormap
upper = mpl.cm.Blues(np.arange(256))
lower = np.ones((int(256/4),4))
for i in range(3):
    lower[:,i] = np.linspace(1, upper[0,i], lower.shape[0])
cmap0 = np.vstack(( lower, upper ))
cmap0 = mpl.colors.ListedColormap(cmap0, name='myColorMap0', N=cmap0.shape[0])

plt.style.use(['science'])

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",  
    "font.serif": "times new roman",
    "mathtext.fontset":"stix",
    "font.size":12,
    "savefig.bbox": "standard"})
plt.rcParams['figure.figsize'] = (6.0, 4.0) # 设置figure_size尺寸
plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
plt.rcParams['savefig.dpi'] = 100 #图片像素
plt.rcParams['figure.dpi'] = 200 #分辨率

col_width = 3.375 # inch(半个A4宽度)
fs = np.array([10,9,6.7])*2

def plot_data_labview(path,fs=2,label='123',i=1,start=0,end=-1,label2='inloop',nfft_n=1024):
    # 读取隔音箱温度随时间变化数据
    t_a=[]
    t_2=[]
    f_1_d=[]
    with open(path,'r') as file:
        next(file)
        userlines = file.readlines()
        file.close()
        for line in userlines:
            datetime_obj = datetime.strptime(line.split('\t')[0], "%Y-%m-%d %H:%M:%S.%f")
            t_a.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
            t_2.append(datetime_obj)
            f_1_d.append(float(line.split('\t')[i])) 
    t_a=t_a[start:end]
    t_2=t_2[start:end]
    f_1_d=f_1_d[start:end]
    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Cavity drift ('+label2+')')
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (K)') 
    plt.plot(t_2,np.array(f_1_d)-np.mean(f_1_d),label=label)
    plt.xticks(rotation=30)
    # plt.ylim([-0.01,0.01])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_vacuum.png')

    taus_1,adevs_1,error_1=allan_adev(f_1_d,fs)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)

    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,Pxx_1,label=label)
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Temperature stability ('+label2+')')
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Power Spectral Density($K^2/Hz$)")
    # plt.xlim([1E-3,0.2])
    # plt.ylim([-32,2])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_PSD_vacuum.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1),np.array(error_1),fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('Temperature stability ('+label2+')')
    #plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_AD_vacuum.png')

def temp_read_psd_allan_2(path,fs=2,label='123',i=1,start=0,end=-1,label2='inloop',nfft_n=1024):
    # 读取隔音箱温度随时间变化数据
    t_a=[]
    t_2=[]
    f_1_d=[]
    with open(path,'r') as file:
        next(file)
        userlines = file.readlines()
        file.close()
        for line in userlines:
            datetime_obj = datetime.strptime(line.split('\t')[0], "%Y-%m-%d %H:%M:%S.%f")
            t_a.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
            t_2.append(datetime_obj)
            f_1_d.append(float(line.split('\t')[i])) 
    t_a=t_a[start:end]
    t_2=t_2[start:end]
    f_1_d=f_1_d[start:end]
    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Temperature stability ('+label2+')')
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (K)') 
    plt.plot(t_2,np.array(f_1_d)-np.mean(f_1_d),label=label)
    plt.xticks(rotation=30)
    # plt.ylim([-0.01,0.01])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_vacuum.png')

    taus_1,adevs_1,error_1=allan_adev(f_1_d,fs)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)

    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,Pxx_1,label=label)
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Temperature stability ('+label2+')')
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Power Spectral Density($K^2/Hz$)")
    # plt.xlim([1E-3,0.2])
    # plt.ylim([-32,2])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_PSD_vacuum.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1),np.array(error_1),fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('Temperature stability ('+label2+')')
    #plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    plt.legend(loc=(1,0))
    # plt.savefig('./temp_AD_vacuum.png')

    
    D_t,alpha,t_x,sigma_y=transfer_temp(t_a,f_1_d,123.85,5.4E5,0.1,fs)
    plt.figure(4)
    plt.plot(t_x,np.sqrt(sigma_y)*alpha,'.-',label=label+"_$\Delta$T={:.2f}".format(D_t))
    # plt.axhline(y=3E-17,color='r',linestyle='--')
    plt.xlim([1,1000])
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Time inteval(s)')
    plt.ylabel('Allan Deviation') 
    plt.title('Allan Deviation of Frequency instability by Temperature')
    plt.grid(which='both',linestyle='dashed') 
    plt.legend()

def transfer_temp(t_a,T_a,t_0,tau,D_t,fs):# tau:s,time transfer constant;#D_t: Temp offset
    num_t,dt,nu,S_out=PSD(t_a,T_a,fs)
    # calculate the time transfer constant \tau and CTE \alpha
    beta=1.8E-8 # /K^2
    t_0=123.85 # K,zero-crossing temperature
    # t_mean=np.mean(T_a) # actual= average temp
    alpha=beta*D_t #/K, coefficient of thermal expansion(CTE)
    # calculate the PSD of Cavity

    S_cav=np.array(S_out[1:])/(1+(np.array(nu[1:])*tau)**2)

    # calculate the allan deviation of Frequency by using PSD
    num_dot=int(np.log2(num_t))
    t_x=2**np.linspace(0,num_dot-1,num_dot)*dt
    df=nu[1]-nu[0]
    a_t_x=np.array([t_x]).T
    a_nu=np.array([nu[1:]])
    a_S_cav=np.array([S_cav])
    sigma_y=2*df*np.sum((np.sin(np.pi*a_t_x*a_nu)**4/(np.pi*a_t_x*a_nu)**2)*a_S_cav,axis=1)

    return D_t,alpha,t_x,sigma_y

def PSD(t_a,T_a,fs):
        tot=t_a[-1]-t_a[0]
        num_t=len(t_a)
        dt=tot/num_t
        nu=np.linspace(0,fs/2,int(len(t_a)/2)+1)
        yy=fft(T_a)
        S_out=np.power(abs(yy[0:int(num_t/2)+1]*dt),2)/tot
        S_out[1:]=2*S_out[1:]
        return num_t,dt,nu,S_out

# sr780数据读取，保存时纵坐标为dBm
def data_read_SR780_dbm(path,label1='123',d_k=1E-5):
    nu_0=[]
    p_dbm=[]
    p_mw=[]
    p_v2=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for line in userlines[3:]:
        nu_0.append(float(line.split('\t')[0]))
        p_dbm.append(float(line.split('\t')[1]))  #unit:dBm
        p_mw.append(10**(float(line.split('\t')[1])/10))  #unit:mW
        p_v2.append(0.25*10**(float(line.split('\t')[1])/10))  #unit:V^2, 系数0.25来自jwc

    df=nu_0[1]-nu_0[0]
    p_v2_Hz=np.array(p_v2)/df/(d_k*429.228E12)**2 #unit:V^2/Hz

    t_x=np.linspace(1/(2*nu_0[-1]),1/(2*nu_0[0]),len(nu_0))  # tau
    sigma_f=[]
    for t_x_i in t_x:
        sigma_f.append(np.sqrt(2*df*np.dot(np.sin(np.pi*t_x_i*np.array(nu_0))**4/(np.pi*t_x_i*np.array(nu_0))**2,np.array(p_v2)))/d_k/429.228E12)  #unit: (Pxx's unit)^2

    plt.figure(1)
    plt.plot(nu_0,p_dbm,label=label1)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude (dBm)')
    plt.xscale('log')
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc='best')

    plt.figure(3)
    plt.plot(nu_0,p_v2_Hz,label=label1)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude ($Hz^{-1}$)')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc='best')

    # plt.figure(4)
    # plt.plot(t_x,sigma_f,label=label1)
    # plt.xlabel('Average time (s)')
    # plt.ylabel('Fractional frequency')
    # plt.xscale('log')
    # plt.yscale('log')
    # plt.grid(which='both',linestyle='dashed') #是否产生网格
    # plt.legend(loc='upper left')

    return nu_0,p_v2_Hz

## sr780数据拼接
def SR780_data_concatenate(nu_a=[0,1],nu_b=[0,1],nu_c=[0,1],nu_d=[0,1],psd_a=[0,1],psd_b=[0,1],psd_c=[0,1],psd_d=[0,1],label1='up_light_far_off_resonant'):
    nu_all=[]
    psd_all=[]
    nu_all=nu_a+nu_b+nu_c+nu_d
    psd_all=np.concatenate((psd_a,psd_b,psd_c,psd_d))

    # df=(nu_all[-1]-nu_all[0])/len(nu_all)
    t_x=np.linspace(1/(2*nu_all[-1]),1/(2*nu_all[0]),len(nu_all))  # tau
    # sigma_f=[]
    # for t_x_i in t_x:
    #     sigma_f.append(np.sqrt(2*df*np.dot(np.sin(np.pi*t_x_i*np.array(nu_all))**4/(np.pi*t_x_i*np.array(nu_all))**2,np.array(psd_all))))  #unit: (Pxx's unit)^2

    df_1=nu_a[1]-nu_a[0]
    df_2=nu_b[1]-nu_b[0]
    df_3=nu_c[1]-nu_c[0]
    df_4=nu_d[1]-nu_d[0]
    sigma_f_2=[]
    for t_x_i in t_x:
        sigma_f_2.append(np.sqrt(2*df_1*np.dot(np.sin(np.pi*t_x_i*np.array(nu_a))**4/(np.pi*t_x_i*np.array(nu_a))**2,np.array(psd_a))
                                +2*df_2*np.dot(np.sin(np.pi*t_x_i*np.array(nu_b))**4/(np.pi*t_x_i*np.array(nu_b))**2,np.array(psd_b))
                                +2*df_3*np.dot(np.sin(np.pi*t_x_i*np.array(nu_c))**4/(np.pi*t_x_i*np.array(nu_c))**2,np.array(psd_c))
                                +2*df_4*np.dot(np.sin(np.pi*t_x_i*np.array(nu_d))**4/(np.pi*t_x_i*np.array(nu_d))**2,np.array(psd_d))))  #unit: (Pxx's unit)^2  


    plt.figure(5)
    plt.plot(nu_all,psd_all,label=label1)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude ($Hz^{-1}$)')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc='best')

    # plt.figure(6)
    # plt.plot(t_x,sigma_f,label=i)
    # plt.xlabel('Average time (s)')
    # plt.ylabel('Fractional frequency')
    # plt.xscale('log')
    # plt.yscale('log')
    # plt.grid(which='both',linestyle='dashed') #是否产生网格
    # plt.legend(loc='lower left')

    plt.figure(7)
    plt.plot(t_x,sigma_f_2,label=label1)
    plt.xlabel('Average time (s)')
    plt.ylabel('Fractional frequency')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc='best')

def sin_func(t,A,omega,phi,C):
    return A*np.sin(omega*t+phi)+C

## 鉴频斜率拟合计算
def freq_disc_slope(path,fs,V,f_mod):
    t_0=[]
    t_data_0=[]
    f_1_0=[]
    f_2_0=[]
    f_3_0=[]
    t_b=[]
    t_0,t_data_0,f_3_0=KK_data_read_single(path,fs,0*fs,10*fs,i=5)
    t_a,f_3_d,d_23=move_long_drift(t_0,f_3_0,0) #1表示打开长漂补偿，0表示不开
    for i in range(len(f_3_d)):
        t_b.append(i/fs)
    A_0,omega_0,phi_0,C_0=optimize.curve_fit(sin_func,t_b,np.array(f_3_d)-f_3_d[0],bounds=([0,2*np.pi*(f_mod-0.01),0,-600],[8000,2*np.pi*(f_mod+0.01),2*np.pi,600]))[0]

    plt.scatter(t_b,np.array(f_3_d)-f_3_d[0])
    plt.plot(np.array(t_b),sin_func(np.array(t_b),A_0,omega_0,phi_0,C_0),'r')

    return V/(2*A_0)

def plot_pico_USB_err(path,switch,label,fs,k_p,title,start,end,nfft_n=1024):#switch:1表示打开长漂补偿，0表示不开
    t=[]
    f=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for line in userlines[3:-1]:
        t.append(float(line.split(',')[0]))
        f.append(float(line.split(',')[1]))

    t_a,f_1_d,d_13=move_long_drift(t[start:end],f[start:end],switch) 
    print(d_13)

    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Light intensity stability ('+title+')')
    plt.xlabel('Time (s)')
    plt.ylabel('$\Delta f/f$') 
    plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)-f_1_d[0],label=label)
    #axes1.set_ylim([-20000,0])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))

    taus_1,adevs_1,error_1=allan_adev(t_a,f_1_d)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)


    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,np.array(Pxx_1)*k_p**2,label=label)
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Light intensity stability ('+title+')')
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Power Spectral Density($V^2/Hz$)")
    plt.xlim([0.001,fs/2])
    #plt.ylim([-27,3])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/PSD_beat_frequency_'+data1+'_'+data3+'.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1)*k_p,np.array(error_1)*k_p,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('Light intensity stability ('+title+')')
    #plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/ad_beat_frequency_'+data1+'_'+data3+'.png')

    return t_a,f_1_d

def plot_keysight_USB_power(path,switch,label,fs,k_p,title,start,end,factor=1,nfft_n=1024,switch2=1,width=100):#switch:1表示打开长漂补偿，0表示不开
    t,f=keysight_data_read(path,fs)
    t_a_m,f_1_d_m,d_13=move_long_drift(t[start:end],f[start:end],switch) 

    t_a=[]
    f_1_d=[]
    buttom=switch2
    if buttom==1:
        f_1_d_mean=np.mean(f_1_d_m[0:300])
        for i in range (0,len(f_1_d_m)):
            if np.abs(f_1_d_mean-f_1_d_m[i])<=width:
                t_a.append(t_a_m[i])
                f_1_d.append(f_1_d_m[i])
    else:
        t_a=t_a_m
        f_1_d=f_1_d_m
    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Frequency changes with time ('+title+')')
    plt.xlabel('Time (h)')
    plt.ylabel('Beat frequency (Hz)') 
    plt.plot((np.array(t_a)-t_a[0])/3600,np.array(f_1_d)*factor,label=label)
    #axes1.set_ylim([-20000,0])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))

    taus_1,adevs_1,error_1=allan_adev(f_1_d,fs)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)


    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,np.array(Pxx_1)*k_p**2,label=label)
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Stability ('+title+')')
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Power Spectral Density($Hz^2/Hz$)")
    plt.xlim([0.001,fs/2])
    fit_line=[]
    # for i in f_1:
    #     fit_line.append(1.6E-31/i)
    # plt.plot(f_1,fit_line,'r',linestyle='--')
    #plt.ylim([-27,3])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    # plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/PSD_beat_frequency_'+data1+'_'+data3+'.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1)*k_p,np.array(error_1)*k_p,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('Stability ('+title+')')
    #plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    # plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/ad_beat_frequency_'+data1+'_'+data3+'.png')
    print(adevs_1[3]*k_p)

    return f_1,np.array(Pxx_1)*k_p**2

def plot_keysight_six_half_USB_power(path,switch,label,fs,k_p,title,start,end,factor=1,nfft_n=1024,switch2=1,width=100):#switch:1表示打开长漂补偿，0表示不开
    t,f=keysight_data_read(path,fs)
    t_a_m,f_1_d_m,d_13=move_long_drift(t[start:end],f[start:end],switch) 

    t_a=[]
    f_1_d=[]
    buttom=switch2
    if buttom==1:
        f_1_d_mean=np.mean(f_1_d_m[0:300])
        for i in range (0,len(f_1_d_m)):
            if np.abs(f_1_d_mean-f_1_d_m[i])<=width:
                t_a.append(t_a_m[i])
                f_1_d.append(f_1_d_m[i])
    else:
        t_a=t_a_m
        f_1_d=f_1_d_m
    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Frequency changes with time ('+title+')')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)') 
    plt.plot(np.array(t_a)-t_a[0],(np.array(f_1_d)-f_1_d[0])*factor,label=label)
    #axes1.set_ylim([-20000,0])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    # plt.legend(loc=(1,0))

    taus_1,adevs_1,error_1=allan_adev(t_a,f_1_d)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)


    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,np.array(Pxx_1)*k_p**2,label=label)
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Stability ('+title+')')
    plt.xlabel("Voltage (V)")
    plt.ylabel("Power Spectral Density($V^2/Hz$)")
    plt.xlim([0.001,fs/2])
    fit_line=[]
    # for i in f_1:
    #     fit_line.append(1.6E-31/i)
    # plt.plot(f_1,fit_line,'r',linestyle='--')
    #plt.ylim([-27,3])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    # plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/PSD_beat_frequency_'+data1+'_'+data3+'.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1)*k_p,np.array(error_1)*k_p,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('Stability ('+title+')')
    #plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    # plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/ad_beat_frequency_'+data1+'_'+data3+'.png')
    print(adevs_1[3]*k_p)

    return f_1,np.array(Pxx_1)*k_p**2

def plot_sim_keysight_USB_power(path,switch,label1='123',fs=1,k_p=1,title='123',start=0,end=-1,nfft_n=1024):#switch:1表示打开长漂补偿，0表示不开
    t,f=sim_keysight_data_read(path,fs)
    t_a,f_1_d,d_13=move_long_drift(t[start:end],f[start:end],switch) 

    plt.figure(0)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Light intensity stability ('+title+')')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)') 
    plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d),label=label1)
    #axes1.set_ylim([-20000,0])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))

    plt.figure(1)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.title('Light intensity stability ('+title+')')
    plt.xlabel('Time (s)')
    plt.ylabel('$\Delta f/f$') 
    plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)*k_p,label=label1)
    #axes1.set_ylim([-20000,0])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))

    taus_1,adevs_1,error_1=allan_adev(t_a,f_1_d)
    f_1,Pxx_1=signal.welch(np.array(f_1_d)-np.mean(f_1_d),fs,window='hann',nperseg=nfft_n,nfft=nfft_n)
    (taus_a, adevs_a,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)


    plt.figure(2)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.plot(f_1,np.array(Pxx_1)*k_p**2,label=label1)
    # fit_line=[]
    # for i in f_1:
    #     fit_line.append(1.6E-31/i)
    # plt.plot(f_1,fit_line,'r',linestyle='--')
    plt.xscale('log')
    plt.yscale('log')
    plt.title('Stability ('+title+')')
    plt.xlabel("Frequency(Hz)")
    plt.ylabel("Power Spectral Density($V^2/Hz$)")
    plt.xlim([0.01,50])
    #plt.ylim([-27,3])
    plt.grid(which='both',linestyle='dashed') #是否产生网格
    plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/PSD_beat_frequency_'+data1+'_'+data3+'.png')

    plt.figure(3)
    # plt.figure(figsize=[9, 6], facecolor='w')
    plt.errorbar(taus_1,np.array(adevs_1)*k_p,np.array(error_1)*k_p,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
    plt.yscale('log')
    plt.xscale('log')
    #plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
    plt.xlabel('Averaging Time(s)')
    plt.ylabel('Allan Deviation $\sigma_y$') 
    plt.title('stability ('+title+')')
    plt.xlim([1E-2,1E2])
    # plt.ylim([1E-16,5E-15])
    plt.grid(which='both',linestyle='dashed') 
    plt.legend(loc=(1,0))
    #plt.savefig(r'E:/zxq/U3/u3/photo/ad_beat_frequency_'+data1+'_'+data3+'.png')

    return adevs_a

## 相噪仪相噪读取及PSD转换
def pn_plot_to_psd(path):
    nu=[]
    pn=[]
    psd=[]
    with open(path,'r',encoding='gbk') as file:
        userlines = file.readlines()
        file.close()
    for i in range(len(userlines)):
        nu.append(float(userlines[i].split(',')[0]))
        pn.append(float(userlines[i].split(',')[1]))
    pn_rad=2*10**(np.array(pn)/10)
    for i in range(len(nu)):
        psd.append(pn_rad[i]*nu[i]**2)
    return nu,pn,psd


## 示波器频率数据读取
def oscilloscope_data_read(path,fs):
    t=[]
    f=[]
    with open(path,'r',encoding='gbk') as file:
        next(file)
        userlines = file.readlines()
        file.close()
    for i in range(len(userlines[0:50E5])):
        t.append(i/fs)
        f.append(float(userlines[i].split(',')[1]))
    
    return t,f

def K_K_plot(path,fs,CH='CH1',label1='123',start=1,end=10,nu_0=429.228E12,nfft_0=1024*4,switch1=0):


    t,t_data,f_1=KK_data_read_single(path,fs,start,end,channel=CH)
    t_a,f_1_d,d_13=move_long_drift(t,f_1,switch1) #1表示打开长漂补偿，0表示不开

    if CH=='CH1':
        plt.figure(1)
        plt.title('Beat Frequency ('+label1+')')
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)-f_1_d[0],label=label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))

        taus_a3,adevs_a3,error_a3=allan_adev(f_1_d,fs)
        taus_m3,adevs_m3,error_m3=allan_mdev(f_1_d,fs)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)
        (taus_1, mdevs_1,errors_1, ns_1) = alt.mdev(f_1_d, rate=fs, data_type="freq", taus=1)
        

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,P_m_13/nu_0**2,label=label1)
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U3 and Si1')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($\sigma_y/\sqrt{Hz}$)")
        plt.xlim([1E-5,100])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        # plt.xlim([1E-1,1E2])  
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(np.array(adevs_1)/nu_0,np.array(mdevs_1)/nu_0)

    if CH=='CH1-2':
        plt.figure(1)
        plt.title('Beat Frequency of U3 and Si1')
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)-f_1_d[0],label=label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))

        taus_a3,adevs_a3,error_a3=allan_adev(f_1_d,fs)
        taus_m3,adevs_m3,error_m3=allan_mdev(f_1_d,fs)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)
        

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,P_m_13/nu_0**2,label=label1)
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U3 and Si1')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($\sigma_y/\sqrt{Hz}$)")
        plt.xlim([1E-3,100])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        # plt.xlim([1E-1,1E2])  
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(np.array(adevs_a3[8])/nu_0,np.array(adevs_m3[8])/nu_0)

    elif CH=='CH2':
        plt.figure(1)
        plt.title('Beat Frequency of U1 and U3')
        plt.xticks(rotation=30)
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t)-t[0],np.array(f_1_d)-f_1_d[0],label=label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc='upper left')

        taus_a3,adevs_a3,error_a3=allan_adev(t_a,f_1_d)
        taus_m3,adevs_m3,error_m3=allan_mdev(t_a,f_1_d)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,np.array(P_m_13)/nu_0**2,label=label1)
        fit_line=[]
        for i in freq_m_13:
            fit_line.append(1.6E-31/i)
        plt.plot(freq_m_13,fit_line,'r',linestyle='--')
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U1 and U3')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($Hz^{-1}$)")
        plt.xlim([1E-2,50])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc='best')
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U1 and U3')
        # plt.ylim([1E-16,1E-14])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc="lower left")
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U1 and U3')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc="best")
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(np.array(adevs_a3[8])/nu_0,np.array(adevs_m3[8])/nu_0)

    elif CH=='CH3':
        plt.figure(1)
        plt.title('Beat Frequency of U1 and Si1')
        plt.xlabel('Time (s)')
        plt.xticks(rotation=30)
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)-f_1_d[0],label='Si1&U1'+label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))

        taus_a3,adevs_a3,error_a3=allan_adev(f_1_d,fs)
        taus_m3,adevs_m3,error_m3=allan_mdev(f_1_d,fs)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,np.array(P_m_13)/nu_0**2,label='Si1&U1'+label1)
        fit_line=[]
        for i in freq_m_13:
            fit_line.append(1.6E-31/i)
        plt.plot(freq_m_13,fit_line,'r',linestyle='--')
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U1 and Si1')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($Hz^{-1}$)")
        plt.xlim([1E-2,50])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='Si1&U1'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U1 and Si1')
        # plt.xlim([1E-2,100])
        # plt.ylim([1E-16,2E-14])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='Si1&U1'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U1 and Si1')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(adevs_1/nu_0)

    return freq_m_13,np.array(P_m_13)/nu_0**2,taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0

def K_K_plot_path1_path2(path1,path2,fs,CH='CH1',label1='123',start=1,end=10,nu_0=429.228E12,nfft_0=1024*4,switch1=0,buttom=0,width=30):


    t_a,t_data_a,f_1_a=KK_data_read_single(path1,fs,0,-1,channel=CH)
    t_b,t_data_b,f_1_b=KK_data_read_single(path2,fs,0,-1,channel=CH)
    t=t_a+t_b
    t=t[start:end]
    t_data_m=t_data_a+t_data_b
    t_data_m=t_data_m[start:end]
    f_1=f_1_a+f_1_b
    f_1=f_1[start:end]
    t_a_m,f_1_d_m,d_13=move_long_drift(t,f_1,switch1) #1表示打开长漂补偿，0表示不开
    print('Drift is {:.3f}mHz/s'.format(-d_13*1000))

    f_1_d=[]
    t_data=[]
    t_a=[]
    if buttom==1:
        f_1_d_m_mean=np.mean(f_1_d_m[-30000:-1])
        for i in range (0,len(f_1_d_m)):
            if np.abs(f_1_d_m_mean-f_1_d_m[i])<=width:
                t_a.append(t_a_m[i])
                t_data.append(t_data_m[i])
                f_1_d.append(f_1_d_m[i])
    else:
        t_a=t_a_m
        t_data=t_data_m
        f_1_d=f_1_d_m

    if CH=='CH1':
        plt.figure(1)
        plt.title('Beat Frequency of U3 and Si1')
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t)-t[0],np.array(f_1_d)-f_1_d[0],label=label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc='upper left')

        taus_a3,adevs_a3,error_a3=allan_adev(t_a,f_1_d)
        taus_m3,adevs_m3,error_m3=allan_mdev(t_a,f_1_d)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)
        

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,P_m_13/nu_0**2,label=label1)
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U3 and Si1')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($\sigma_y/\sqrt{Hz}$)")
        plt.xlim([1E-3,100])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        # plt.xlim([1E-1,1E2])  
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label=label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U3 and Si1')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(np.array(adevs_a3[8])/nu_0,np.array(adevs_m3[8])/nu_0)

    elif CH=='CH2':
        plt.figure(1)
        plt.title('Beat Frequency of U1 and U3')
        plt.xticks(rotation=30)
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t)-t[0],np.array(f_1_d)-f_1_d[0],label='U1&U3')
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc='upper left')

        taus_a3,adevs_a3,error_a3=allan_adev(t_a,f_1_d)
        taus_m3,adevs_m3,error_m3=allan_mdev(t_a,f_1_d)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,np.array(P_m_13)/nu_0**2,label='U1&U3'+label1)
        fit_line=[]
        for i in freq_m_13:
            fit_line.append(1.6E-31/i)
        plt.plot(freq_m_13,fit_line,'r',linestyle='--')
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U1 and U3')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($Hz^{-1}$)")
        plt.xlim([1E-2,50])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc='best')
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='U1&U3'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U1 and U3')
        # plt.ylim([1E-16,1E-14])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc="lower left")
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='U1&U3'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U1 and U3')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc="best")
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

    elif CH=='CH3':
        plt.figure(1)
        plt.title('Beat Frequency of U1 and Si1')
        plt.xlabel('Time (s)')
        plt.xticks(rotation=30)
        plt.ylabel('Frequency(Hz)') 
        plt.plot(np.array(t_a)-t_a[0],np.array(f_1_d)-f_1_d[0],label='Si1&U1'+label1)
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))

        taus_a3,adevs_a3,error_a3=allan_adev(t_a,f_1_d)
        taus_m3,adevs_m3,error_m3=allan_mdev(t_a,f_1_d)
        (taus_1, adevs_1,errors_1, ns_1) = alt.adev(f_1_d, rate=fs, data_type="freq", taus=1)

        P_m_13,freq_m_13=psd_welch(t_a,f_1_d,fs,nfft_0)

        plt.figure(2)
        plt.plot(freq_m_13,np.array(P_m_13)/nu_0**2,label='Si1&U1'+label1)
        fit_line=[]
        for i in freq_m_13:
            fit_line.append(1.6E-31/i)
        plt.plot(freq_m_13,fit_line,'r',linestyle='--')
        plt.xscale('log')
        plt.yscale('log')
        plt.title('Beat Frequency of U1 and Si1')
        plt.xlabel("Frequency(Hz)")
        plt.ylabel("Power Spectral Density($Hz^{-1}$)")
        plt.xlim([1E-2,50])
        # plt.tick_params (labelsize= 14)
        # plt.ylim([-20,15])
        # plt.yticks(range(-20,15,5))
        plt.grid(which='both',linestyle='dashed') #是否产生网格
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_PSD_{:>1d}.png'.format(times))


        plt.figure(3)
        plt.errorbar(taus_a3,np.array(adevs_a3)/nu_0,np.array(error_a3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='Si1&U1'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Allan Deviation $\sigma_y$') 
        plt.title('Allan Deviation of U1 and Si1')
        # plt.xlim([1E-2,100])
        # plt.ylim([1E-16,2E-14])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        plt.figure(4)
        plt.errorbar(taus_m3,np.array(adevs_m3)/nu_0,np.array(error_m3)/nu_0,fmt='o--',ecolor='r',elinewidth=2,capsize=4,label='Si1&U1'+label1)
        plt.yscale('log')
        plt.xscale('log')
        # plt.axhline(y=3E-17,color='r',linestyle='--',label='thermal noise limit')
        plt.xlabel('Averaging Time(s)')
        plt.ylabel('Modified Allan Deviation $\sigma_y$') 
        plt.title('Modified Allan Deviation of U1 and Si1')
        # plt.ylim([4E-16,2E-15])
        plt.grid(which='both',linestyle='dashed') 
        plt.legend(loc=(1,0))
        # plt.savefig(r'beat_fre_U1_U3_Si1_'+data[0]+'_ad_{:>1d}.png'.format(times))

        print(adevs_1/nu_0)

    return adevs_1/nu_0


def psd_welch(t_x,f_x,fs,nfft_0=1024*16*8):
    nu,Pxx=signal.welch(f_x,fs,window='hann',scaling='density',nperseg=0.5*nfft_0,nfft=nfft_0)

    return Pxx,nu #unit：(f_x's unit)^2/Hz, Hz

def psd_int_allan(nu,Pxx): #unit：Hz,(f_x's unit)^2/Hz
    df=nu[1]-nu[0]
    t_x=1  # @1s
    sigma_f=[]
    for i in range(2,len(nu)):
        a_nu=np.array([nu[1:i]])  #unit:Hz
        a_S=np.array([(Pxx[1:i])]) #unit: (Pxx's unit)^2/Hz
        sigma_f.append(2*df*np.sum(np.sin(np.pi*t_x*a_nu)**4/(np.pi*t_x*a_nu)**2*a_S))  #unit: (Pxx's unit)^2

    return nu[2:len(nu)],sigma_f

## CSD(cross power spectral density)函数绘制

def plot_csd(f_13,f_23,fs,f0,nfft):
    f,Pxy1=signal.csd(f_13,f_23,fs,window='hann',nperseg=nfft)
    csd_12=np.array(np.abs(Pxy1))/f0**2

    return f,csd_12

## labview自编程序数据读取：
def labview_data_read(path,fs):
    t=[]
    T=[]
    with open(path,'r') as file:
        next(file)
        userlines = file.readlines()
        file.close()
    for line in userlines:
        datetime_obj = datetime.strptime(line.split('\t')[0], "%Y-%m-%d %H:%M:%S.%f")
        t.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
        T.append(float(line.split('\t')[1])) 
    
    return t,T


## K+K频率计数器数据读取
def KK_data_read(path,fs,begin,end,CH1=3,CH2=4,CH3=5,CH4=6,CH5=8):
    t=[]
    t_data=[]
    f_1=[]
    f_2=[]
    f_3=[]
    f_4=[]
    f_5=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for line in userlines[begin+1:end]:
        datetime_obj = datetime.strptime('20'+line.split()[0]+line.split()[1], "%Y%m%d%H%M%S.%f")
        t.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
        t_data.append(datetime_obj)
        f_1.append(float(line.split()[CH1]))
        f_2.append(float(line.split()[CH2]))
        f_3.append(float(line.split()[CH3]))
        f_4.append(float(line.split()[CH4]))
        f_5.append(float(line.split()[CH5]))
    
    return t,t_data,f_1,f_2,f_3,f_4,f_5

def KK_data_read_single(path,fs,begin,end,channel='CH1'):
    t=[]
    t_data=[]
    f_1=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for line in userlines[begin+1:end]:
        datetime_obj = datetime.strptime('20'+line.split()[0]+line.split()[1], "%Y%m%d%H%M%S.%f")
        t.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
        t_data.append(datetime_obj)
        if channel=='CH1':
            f_1.append(float(line.split()[3]))
        elif channel=='CH2':
            f_1.append(float(line.split()[4]))
        elif channel=='CH3':
            f_1.append(float(line.split()[5]))
        elif channel=='CH1-2':
            f_1.append(float(line.split()[8]))
    
    return t,t_data,f_1

## Keysight频率计数器数据读取
def keysight_data_read(path,fs):
    t=[]
    f=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for i in range(len(userlines)):
        t.append(i/fs)
        f.append(float(userlines[i]))
    
    return t,f

def sim_keysight_data_read(path,fs):
    t=[]
    f=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for i in range(1,len(userlines)):
        t.append(i/fs)
        f.append(float(userlines[i].split(',')[1]))
    
    return t,f

def keysight_six_data_read(path,fs):
    t=[]
    f=[]
    with open(path,'r') as file:
        userlines = file.readlines()
        file.close()
    for i in range(0,len(userlines)):
        t.append(float(userlines[i].split('\t')[0]))
        f.append(float(userlines[i].split('\t')[1]))
    
    return t,f

## 减长漂
def move_long_drift(t_a,f_1,switch,length=100):#switch补长漂开关(0,1)
    f_1_d=[]
    d_13=-(np.mean(f_1[-1*length:-1])-np.mean(f_1[0:length]))/(np.mean(t_a[-1*length:-1])-np.mean(t_a[0:length]))
    for l in range(0,len(t_a)):
        if switch>=1:
            f_1_d.append(f_1[l]+d_13*(t_a[l]-t_a[0]))
        else:
            f_1_d.append(f_1[l])#+d_13*(t_a[l]-t_a[0])
    return t_a,f_1_d,d_13

## 定义一元一次函数
def line_fit(x,a,b):
    
    return a*x+b

## 线性拟合
def calculate_slope(v_in,k_p_1):
    A1, B1=optimize.curve_fit(line_fit,v_in,k_p_1)[0]
    v_in_0=np.arange(np.min(v_in)-(np.max(v_in)-np.min(v_in))/100,np.max(v_in)+(np.max(v_in)-np.min(v_in))/100,(np.max(v_in)-np.min(v_in))/100)
    k_p_1_fit=line_fit(v_in_0,A1,B1)

    return v_in,k_p_1_fit,A1,B1

## 已知(t_x,f_x)计算ad，带errorbar(x表示pressure、temperature等)
def allan_adev(f_x,fs):
    # tot=t_x[-1]-t_x[0]
    # num_t=len(t_x)
    dt=1/fs
    # num_dot=int(np.log2(num_t))
    t_n=np.array([1,2,5,8,10,20,50,80,100,200,500,800,1000,2000,5000,8000,10000,20000,50000,80000])*dt
    (taus, adevs,errors, ns) = alt.adev(f_x, rate=fs, data_type="freq", taus=t_n)
    cis=[]
    for (t,dev) in zip(taus,adevs):
        edf = alt.edf_greenhall(alpha=0, d=2, m=round(t/taus[0]), N=len(f_x), overlapping=False, modified=False)
        (lo, hi) = alt.confidence_interval(dev=dev, edf=edf)
        cis.append((lo, hi))
    err_lo = np.array([d - ci[0] for (d, ci) in zip(adevs, cis)])
    err_hi = np.array([ci[1] - d for (d, ci) in zip(adevs, cis)])
    error=[err_lo,err_hi]
    return taus,adevs,error

def allan_oadev(f_x,fs):
    # tot=t_x[-1]-t_x[0]
    # num_t=len(t_x)
    dt=1/fs
    # num_dot=int(np.log2(num_t))
    t_n=np.array([1,2,5,8,10,20,50,80,100,200,500,800,1000,2000,5000,8000,10000,20000,50000,80000])*dt
    (taus, adevs, errors, ns) = alt.oadev(f_x, rate=fs, data_type="freq", taus=t_n)
    cis=[]
    for (t,dev) in zip(taus,adevs):
        edf = alt.edf_greenhall(alpha=0, d=2, m=round(t/taus[0]), N=len(f_x), overlapping=True, modified=False)
        (lo, hi) = alt.confidence_interval(dev=dev, edf=edf)
        cis.append((lo, hi))
    err_lo = np.array([d - ci[0] for (d, ci) in zip(adevs, cis)])
    err_hi = np.array([ci[1] - d for (d, ci) in zip(adevs, cis)])
    error=[err_lo,err_hi]
    return taus,adevs,error

def allan_mdev(f_x,fs):
    # tot=t_x[-1]-t_x[0]
    # num_t=len(t_x)
    dt=1/fs
    # num_dot=int(np.log2(num_t))
    t_n=np.array([1,2,5,8,10,20,50,80,100,200,500,800,1000,2000,5000,8000,10000,20000,50000,80000])*dt
    (taus, adevs, errors, ns) = alt.mdev(f_x, rate=fs, data_type="freq", taus=t_n)
    cis=[]
    for (t,dev) in zip(taus,adevs):
        edf = alt.edf_greenhall(alpha=0, d=2, m=round(t/taus[0]), N=len(f_x), overlapping=False, modified=True)
        (lo, hi) = alt.confidence_interval(dev=dev, edf=edf)
        cis.append((lo, hi))
    err_lo = np.array([d - ci[0] for (d, ci) in zip(adevs, cis)])
    err_hi = np.array([ci[1] - d for (d, ci) in zip(adevs, cis)])
    error=[err_lo,err_hi]
    return taus,adevs,error

def allan_hdev(f_x,fs):
    # tot=t_x[-1]-t_x[0]
    # num_t=len(t_x)
    dt=1/fs
    # num_dot=int(np.log2(num_t))
    t_n=np.array([1,2,5,8,10,20,50,80,100,200,500,800,1000,2000,5000,8000,10000,20000,50000,80000])*dt
    (taus, adevs, errors, ns) = alt.hdev(f_x, rate=fs, data_type="freq", taus=t_n)
    cis=[]
    for (t,dev) in zip(taus,adevs):
        edf = alt.edf_greenhall(alpha=0, d=2, m=round(t/taus[0]), N=len(f_x), overlapping=False, modified=True)
        (lo, hi) = alt.confidence_interval(dev=dev, edf=edf)
        cis.append((lo, hi))
    err_lo = np.array([d - ci[0] for (d, ci) in zip(adevs, cis)])
    err_hi = np.array([ci[1] - d for (d, ci) in zip(adevs, cis)])
    error=[err_lo,err_hi]
    return taus,adevs,error


## 已知(t_x,f_x)计算psd，带errorbar(x表示pressure、temperature等)
def allan_psd(t_x,f_x,label,nfft=1024):
    tot=t_x[-1]-t_x[0]
    num_t=len(t_x)
    dt=tot/num_t
    fs=1/dt
    Pxx,nu=plt.psd(f_x,NFFT=nfft,Fs=fs,detrend='mean',window=np.hanning(nfft),noverlap=int(nfft*3/4),sides='onesided',label=label)

    return Pxx,nu

    
def way_one_plus_and_minus(taus,U12,U23,U13):
    U1=[]
    U2=[]
    U3=[]
    for i in range(0,len(U23)):
        U1.append(np.sqrt((U12[i]**2+U13[i]**2-U23[i]**2)/2))
        U2.append(np.sqrt((U12[i]**2+U23[i]**2-U13[i]**2)/2))
        U3.append(np.sqrt((U13[i]**2+U23[i]**2-U12[i]**2)/2))

    return taus,U1,U2,U3

#定义一元六次方程
def solve_equ(c1,c2,c3,c4,c5,c6):
    x=sp.Symbol('x')
    f=c1*x+c2*x**2+c3*x**3+c4*x**4+c5*x**5+c6*x**6
    x=sp.solve(f)

    return x

#定义三角帽函数
def three_cornered_hat(f_1_d,f_2_d,fs):
    # 以U3为参考：
    s_11=[]
    s_22=[]
    s_12=[]
    S=[]
    # tot=t_1[-1]-t_1[0]
    # num_t=len(t_1)
    # dt=tot/num_t
    # num_dot=int(np.log2(num_t))
    # taus_s=2**np.linspace(0,num_dot-1,num_dot)*dt
    dt=1/fs
    tau_s=np.array([1,2,5,8,10,20,50,80,100,200,500,800,1000,2000,5000,8000,10000,20000,50000,80000])*dt
    for i in range(0,len(tau_s)):
        d_mean_U13=[]
        d_mean_U23=[]
        s_s_1=[]
        s_s_2=[]
        s_s_12=[]
        for j in range(1,int(len(f_1_d)/int(tau_s[i]*fs))):
            d_mean_U13.append(np.mean(f_1_d[int(tau_s[i]*fs)*j:(j+1)*int(tau_s[i]*fs)])-np.mean(f_1_d[(j-1)*int(tau_s[i]*fs):j*int(tau_s[i]*fs)]))
            d_mean_U23.append(np.mean(f_2_d[int(tau_s[i]*fs)*j:(j+1)*int(tau_s[i]*fs)])-np.mean(f_2_d[(j-1)*int(tau_s[i]*fs):j*int(tau_s[i]*fs)]))
        for k in range(0,len(d_mean_U13)):
            s_s_1.append(d_mean_U13[k]**2)
            s_s_2.append(d_mean_U23[k]**2)
            s_s_12.append(d_mean_U13[k]*d_mean_U23[k])
        s_11.append(np.mean(s_s_1)/2)
        s_22.append(np.mean(s_s_2)/2)
        s_12.append(np.mean(s_s_12)/2)
        S.append(s_11[i]*s_22[i]-s_12[i]**2)

    # 计算c    
    c_1=[]
    c_2=[]
    c_3=[]
    c_4=[]
    c_5=[]
    c_6=[]
    for i in range(0,len(s_11)):
        c_1.append(3*((S[i])**0.5)*s_12[i]*(s_11[i]-s_12[i])*(s_22[i]-s_12[i]))
        c_2.append(2.25*(S[i]**2)+2*(s_11[i]+s_22[i]+s_12[i])*c_1[i]/(3*(S[i]**0.5)))
        c_3.append(3*(S[i]**1.5)*(s_11[i]+s_22[i])+c_1[i]/3)
        c_4.append(S[i]*(1.5*S[i]+(s_11[i]+s_22[i]-s_12[i])*(s_11[i]+s_22[i]+s_12[i])))
        c_5.append((S[i]**1.5)*(s_11[i]+s_22[i]))
        c_6.append((S[i]**2)/4)

    # 解方程
    f_solve=[]
    for i in range (0,len(c_1)):
        f_solve.append(solve_equ(c_1[i],c_2[i],c_3[i],c_4[i],c_5[i],c_6[i]))

    f_solve_deal=np.zeros((len(f_solve),len(f_solve[0])))
    for i in range(0,len(f_solve)):
        for j in range(0,len(f_solve[i])):
            if f_solve[i][j]>0:
                f_solve_deal[i][j]=f_solve[i][j]
            else:
                f_solve_deal[i][j]=0
    # 求最小正根
    f_min_plus=[]
    for line in f_solve_deal:
        if np.max(line)>0:
            temp=[]
            for i in line:
                if i>0:
                    temp.append(i)
            f_min_plus.append(np.min(temp))
        else:
            f_min_plus.append(0)

    ## 计算b
    b_0=[]
    b_1=[]
    b_2=[]
    for i in range(0,len(f_min_plus)):
        b_0.append((S[i]**0.5)*(s_12[i]**2)+(s_12[i]**2)*(s_11[i]+s_22[i])*f_min_plus[i]+(S[i]**0.5)*(s_12[i]**2)*(f_min_plus[i]**2))
        b_1.append(-(S[i]**0.5)*s_12[i]-(2*s_12[i]**2+1.5*S[i])*f_min_plus[i]-(S[i]**0.5)*(s_11[i]+s_22[i])*(f_min_plus[i]**2)-S[i]*(f_min_plus[i]**3)/2)
        b_2.append((S[i]**0.5)+2*(s_11[i]+s_22[i]-s_12[i])*f_min_plus[i]+3*(S[i]**0.5)*f_min_plus[i]**2)

    ## 计算a,r
    a_20=[]
    a_02=[]
    a_11=[]
    a_10=[]
    r_33=[]
    r_13=[]
    r_23=[]
    for i in range(0,len(b_0)):
        a_20.append(2*S[i]**0.5+f_min_plus[i]*s_22[i])
        a_02.append(2*S[i]**0.5+f_min_plus[i]*s_11[i])
        a_11.append(S[i]**0.5-f_min_plus[i]*s_12[i])
        r_33.append(-b_1[i]/b_2[i])
        a_10.append((S[i]**0.5)*(2*r_33[i]+s_12[i]))
        r_13.append(r_33[i]-a_10[i]*(a_02[i]-a_11[i])/(a_20[i]*a_02[i]-a_11[i]**2))
        r_23.append(r_33[i]-a_10[i]*(a_20[i]-a_11[i])/(a_20[i]*a_02[i]-a_11[i]**2))

    r_11=[]
    r_12=[]
    r_22=[]
    for i in range(0,len(r_13)):
        r_11.append(s_11[i]-r_33[i]+2*r_13[i])
        r_12.append(s_12[i]-r_33[i]+r_13[i]+r_23[i])
        r_22.append(s_22[i]-r_33[i]+2*r_23[i])

    ## 计算u1,u2,u3
    u1=[(i)**0.5 for i in r_11]
    u2=[(i)**0.5 for i in r_22]
    u3=[(i)**0.5 for i in r_33]

    return tau_s,u1,u2,u3