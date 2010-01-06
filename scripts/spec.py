#!/usr/bin/env python
'''
This script demonstrates programming an FPGA, configuring a wideband spectrometer and plotting the received data using the Python KATCP library along with the katcp_wrapper distributed in the corr package. Designed for use with TUT3 at the 2009 CASPER workshop.\n

You need to have KATCP and CORR installed. Get them from http://pypi.python.org/pypi/katcp and http://casper.berkeley.edu/svn/trunk/projects/packetized_correlator/corr-0.4.0/

\nAuthor: Jason Manley, November 2009.
'''

#TODO: add support for ADC histogram plotting.
#TODO: add support for determining ADC input level 

import corr,time,numpy,struct,sys,logging,pylab

bitstream = 'lgspec_16k_2x_2010_Jan_01_2018.bof'
katcp_port=7147

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

    pylab.figure(num=1,figsize=(9,9))
    pylab.ioff()

    max = 0
    max_index = 0

    for i in range(8192):
	if interleave_a[i] < 1:
	    interleave_a[i] = 1
	if i > 10 and interleave_a[i] > max:
	    max = interleave_a[i]
	    max_index = i	    

    print "Index of max value: "+str(max_index)
    
    for i in range(8192):
	if interleave_b[i] < 1:
	    interleave_b[i] = 1


    pylab.subplot(211)
    #pylab.plot(interleave_a)
    pylab.semilogy(interleave_a)
    pylab.title('Integration number %i.'%prev_integration)
    pylab.ylabel('Power (arbitrary units)')
    pylab.grid()
    pylab.xlabel('Channel')
    pylab.xlim(0,8192)

    pylab.subplot(212)
    #pylab.plot(interleave_b)
    pylab.semilogy(interleave_b)
    #pylab.title('Integration number %i.'%prev_integration)
    pylab.ylabel('Power (arbitrary units)')
    pylab.grid()
    pylab.xlabel('Channel')
    pylab.xlim(0,8192)

    pylab.ioff()

    pylab.hold(False)
    pylab.show()
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
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=20,logger=logger)
    time.sleep(2)

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

    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'

    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'

    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
  #      fpga.write_int('quant0_gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'

    time.sleep(2)

    prev_integration = fpga.read_uint('acc_cnt')
    while(1):
        current_integration = fpga.read_uint('acc_cnt')
	diff=current_integration - prev_integration
        if diff==0:
            time.sleep(0.01)
        else:
            if diff > 1:
                print 'WARN: We lost %i integrations!'%(current_integration - prev_integration)
            prev_integration = fpga.read_uint('acc_cnt')
            print 'Grabbing integration number %i'%prev_integration
	    print 'Grabbed it'
            plot_spectrum()

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

