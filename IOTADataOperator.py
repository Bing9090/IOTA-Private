#!/usr/bin/python
# coding:utf-8
import iota
from iota import ProposedTransaction
from iota import Address, Transaction, Iota
from iota import Tag
from iota import TryteString

from iotaParams import *

import logging

logger = logging.getLogger('log')


class IOTADataOperator(object):
    """
    Generate a new address based on the private key
    根据私钥生成一个新的地址
    """

    def generateAddress(self, seed, index):
        api_seed = Iota(iotaNodeUrl, seed)
        # Here index is used to identify the address(这里index用来标识是第几个地址)
        addresses = api_seed.get_new_addresses(index=index, count=1, security_level=2, checksum=True)
        address = addresses['addresses'][0]
        print('\nThe first available address for your seed: %s' % address)

    """
    Send a transaction
    发送一笔交易
    """

    def sendTransaction(self, data, tag):
        # Structure transaction-构造交易
        tx = ProposedTransaction(
            address=Address(iotaAddress),
            message=TryteString.from_unicode(data),
            tag=Tag(tag),
            value=0
        )
        tx = api.prepare_transfer(transfers=[tx])
        result = api.send_trytes(tx['trytes'], depth=iota_depth, min_weight_magnitude=iota_min_weight_magnitude)
        print('Transaction sent to the tangle! result:{}'.format(result))

    """
    Query all transactions in an address and return a list of CovidData objects
    查询某地址所有交易，返回CovidData对象列表
    """

    def findTransactions(self, tag=None):
        logger.info("begin to load covid data")
        transactions = None
        if tag:
            transactions = api.find_transactions(addresses=[iotaAddress, ], tags=[tag, ])
        else:
            transactions = api.find_transactions(addresses=[iotaAddress, ])
        # transactions = api.find_transactions(tags=[covid19model_tag, ])
        hashes = []
        # Determine non-empty address-判断非空地址
        if not transactions:
            logger.info("iotaAddress not exists")
            return []
        else:
            logger.info("loading iotaAddress data...")
        for txhash in transactions['hashes']:
            hashes.append(txhash)
        if hashes:
            logger.info("transactions not empty")
        else:
            logger.info("transactions empty")
            return []
        # Get Trytes accepts multiple Transaction Hashes
        trytes = api.get_trytes(hashes)['trytes']
        # We need to get all trytes from all messages and put them in the right order
        # We do this by looking at the index of the transaction
        parts = []
        for trytestring in trytes:
            tx = Transaction.from_tryte_string(trytestring)
            # logger.info(tx.current_index)
            parts.append((tx.current_index, tx.signature_message_fragment))

        parts.sort(key=lambda x: x[0])

        # All that's left is to concatenate and wrap the parts in a TryteString object
        full_message = TryteString.from_unicode('')

        resultMsgs = []
        for index, part in parts:
            full_message += part
            # Constructed as CovidData-构造为CovidData
            try:
                cm = full_message.decode()
                # Add to result list-添加到结果列表
                resultMsgs.append(cm)
            except iota.codecs.TrytesDecodeError:
                logger.exception("covid data analysis iota.codecs.TrytesDecodeError, data: " + full_message.decode())
                continue
            except ValueError:
                logger.exception("covid data analysis ValueError, data: " + full_message.decode())
                continue
            except TypeError:
                logger.exception("covid data analysis TypeError, data: " + full_message.decode())
                continue
            except:
                logger.exception("covid data analysis error, data: " + full_message.decode())
                continue
            finally:
                # Clear to the next transaction data-清空给下一条交易数据
                full_message = TryteString.from_unicode('')

        return resultMsgs


if __name__ == '__main__':
    # generate a address
    iotaDataOperator = IOTADataOperator()
    iotaDataOperator.generateAddress(seed, 0)
    # send a trans
    iotaDataOperator.sendTransaction("gundam", "TEST")
    # find trans
    transMsgs = iotaDataOperator.findTransactions("TEST")
    print(transMsgs)
