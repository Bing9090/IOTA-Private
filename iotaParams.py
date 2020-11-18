#!/usr/bin/python
# coding:utf-8

"""
IOTA chain params
"""

from iota import Iota

# local iota-private seed
seed = "UMJJGDDTCRHQSVIZPVJDKEFVZZTBXJOBTXBADXTMDBIFRFLCVXWPEH9YHRVNNNGRMKQRNRAZBKNHKHPHI"

# local iota-private
iotaNodeUrl = "http://192.168.8.109:14265"

# local iota-private addr
iotaAddressLst = ["JNCVXQAQKDUORAFITSZGKRYHDMCETBJRQ9TWCEGYJUOAZQHTREADUNKDEIXSEXZVGKQFBUGHAUQLFLWMXPOYPDMXX9"]

iotaAddress = iotaAddressLst[0]

# global api object
api = Iota(iotaNodeUrl)
# params
iota_depth = 8
iota_min_weight_magnitude = 9
# tag only access A-Z/9
typical_tag = ""

