#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2016
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Start the DFMS cluster on Magnus / Galaxy at Pawsey

Current plan (as of 12-April-2016):
    1. Launch a number of Node Managers (NM) using MPI processes
    2. Having the NM MPI processes to send their IP addresses to the Rank 0
       MPI process
    3. Launch the Island Manager (IM) on the Rank 0 MPI process using those IP
       addresses

"""
from mpi4py import MPI
import commands, time

def get_ip():
    """
    This is brittle, but works on Magnus/Galaxy for now
    """
    re = commands.getstatusoutput('ifconfig')
    line = re[1].split('\n')[1]
    return line.split()[1].split(':')[1]

def startNM():
    """
    Start node manager
    """
    time.sleep(5)

def startDIM():
    """
    Start data island manager
    """
    pass

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

ip_adds = get_ip()
if (rank != 0):
    startNM()
else:
    dim_ip = ip_adds

ip_adds = comm.gather(ip_adds, root=0)
if (rank == 0):
    print "A list of IP addresses are: ", ip_adds
    startDIM()