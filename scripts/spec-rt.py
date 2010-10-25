#/isr/bin/env python
'''
Plot SAO spectrometer
Authors: Jason Manley, Mark Wagner
'''

#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import corr,time,numpy,struct,sys,logging,pylab

bitstream = 'lgspec_16k_2x_2010_Sep_11_1805.bof'
katcp_port=7147

#plotting window 
pylab.ion()
pylab.figure(num=1,figsize=(12,12))
x=(numpy.array(range(8192)))*(400./8192)
y=numpy.array(x*10000000)

pylab.subplot(211)
pylab.title('SAO Spectrometer')
pylab.ylabel('Power (arbitrary units)')
pylab.xlabel('Freq (MHz)')
pylab.ylim(0,1000000000000)
pylab.xlim(0,400)
line1,=pylab.semilogy(x,y,color='black')

pylab.subplot(212)
pylab.ylabel('Power (arbitrary units)')
pylab.xlabel('Freq (MHz)')
pylab.ylim(0,1000000000000)
pylab.xlim(0,400)
line2,=pylab.semilogy(x,y,color='black')

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def write_datafile():

    #write data to file (ascii)
    #datafile=open('lgspec.dat','w')
    
    #for i in range(0,size(interleave_a))
#	datafile.write(interleave_a[i])    
#
#    for i in range(0,size(nterleave_b))
#	datafile.write(interleave_b[i])    
    #datafile.close()

    #write data to file (binary)
    a_0=struct.unpack('>4096l',fpga.read('even',4096*4,0))
    a_1=struct.unpack('>4096l',fpga.read('odd',4096*4,0))
    b_0=struct.unpack('>4096l',fpga.read('even1',4096*4,0))
    b_1=struct.unpack('>4096l',fpga.read('odd1',4096*4,0))

    interleave_a=[]
    interleave_b=[]


    for i in range(4096):
        interleave_a.append(a_0[i])
        interleave_a.append(a_1[i])
        interleave_b.append(b_0[i])
        interleave_b.append(b_1[i])

    acc_cnt=fpga.read_int('acc_cnt')

    datafile=open('saospec_i'+str(acc_cnt)+'.bin','wb')
    buf_a=struct.pack(">8192l",*interleave_a)
    #buf_b=struct.pack(">8192l",*interleave_b)

    datafile.write(buf_a)
    #datafile.write(buf_b)
    datafile.close()


def plot_spectrum():

    #get the data...    
    a_0=struct.unpack('>4096l',fpga.read('even',4096*4,0))
    a_1=struct.unpack('>4096l',fpga.read('odd',4096*4,0))
    b_0=struct.unpack('>4096l',fpga.read('even1',4096*4,0))
    b_1=struct.unpack('>4096l',fpga.read('odd1',4096*4,0))

    interleave_a=[]
    interleave_b=[]

    for i in range(4096):
        interleave_a.append(a_0[i])
        interleave_a.append(a_1[i])
        interleave_b.append(b_0[i])
        interleave_b.append(b_1[i])

    max = 0
    max_index = 0

    for i in range(8192):
	if interleave_a[i] < 1:
	    interleave_a[i] = interleave_a[i]*10+1

    if i > 10 and interleave_a[i] > max:
	max = interleave_a[i]
	max_index = i	    

#    print "Index of max value: "+str(max_index)
    
    for i in range(8192):
	if interleave_b[i] < 1:
	    interleave_b[i] = interleave_b[i]*10+1

    pylab.subplot(211)
#    pylab.title('Integration number %i.'%prev_integration)
    line1.set_ydata(interleave_a)
  #  pylab.xlim(0,8192)
    pylab.hold(False)
    pylab.draw()
    
    pylab.subplot(212)
    line2.set_ydata(interleave_b)
  #  pylab.xlim(0,8192)
    #pylab.ioff()

    pylab.hold(False)
    pylab.draw()



#START OF MAIN:

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=2*(2**24)/16384,
        help='Set the number of vectors to accumulate between dumps. default is 2*(2^28)/16384, or just under 2 seconds.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0xffffffff,
        help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. Run with the -h flag to see all options.\nExiting.' 
	exit()
    else:
        roach = args[0]

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, logger=logger)
    time.sleep(3)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA...',
    if not opts.skip:
        fpga.progdev(bitstream)
	
	time.sleep(1)
        print 'done'
    else:
        print 'Skipped.'

    time.sleep(2)
    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'
    #fpga.write_int('acc_len',8192) 

    #configure
    fpga.write_int('sync_period',100663295)
    fpga.write_int('sync_sel',1)

    fpga.write_int('acc_len',16384)
    fpga.write_int('acc_len_sel',1)

    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
  #      fpga.write_int('quant0_gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'


#    prev_integration = fpga.read_uint('acc_cnt')
    while(1):
#        current_integration = fpga.read_uint('acc_cnt')
#	diff=current_integration - prev_integration
#        if diff==0:
#            time.sleep(0.01)
#        else:
#            if diff > 1:
#                print 'WARN: We lost %i integrations!'%(current_integration - prev_integration)
#            prev_integration = fpga.read_uint('acc_cnt')
#            print 'Grabbing integration number %i'%prev_integration
#	    print 'Grabbed it'	
	try:	
	    print "Accumlation num: "+str(fpga.read_int('acc_cnt'))
	    write_datafile()
            #plot_spectrum()

	except RuntimeError:
	    print 'network read error occurred at %s. ignoring.' % time.asctime()


except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

