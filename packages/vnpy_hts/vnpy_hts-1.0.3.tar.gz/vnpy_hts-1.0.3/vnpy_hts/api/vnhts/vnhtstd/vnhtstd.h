#pragma once
//ϵͳ
#ifdef WIN32
#include "pch.h"
#endif

#include "vnhts.h"
#include "pybind11/pybind11.h"
#include "DFITCSECTraderApi.h"

using namespace pybind11;
using namespace std;

//����

#define ONFRONTCONNECTED 0
#define ONFRONTDISCONNECTED 1
#define ONRTNNOTICE 2
#define ONRSPERROR 3
#define ONRSPSTOCKUSERLOGIN 4
#define ONRSPSTOCKUSERLOGOUT 5
#define ONRSPSTOCKUSERPASSWORDUPDATE 6
#define ONRSPSTOCKENTRUSTORDER 7
#define ONRSPSTOCKWITHDRAWORDER 8
#define ONRSPSTOCKQRYENTRUSTORDER 9
#define ONRSPSTOCKQRYREALTIMETRADE 10
#define ONRSPSTOCKQRYSERIALTRADE 11
#define ONRSPSTOCKQRYPOSITION 12
#define ONRSPSTOCKQRYCAPITALACCOUNTINFO 13
#define ONRSPSTOCKQRYACCOUNTINFO 14
#define ONRSPSTOCKQRYSHAREHOLDERINFO 15
#define ONRSPSTOCKTRANSFERFUNDS 16
#define ONRSPSTOCKENTRUSTBATCHORDER 17
#define ONRSPSTOCKWITHDRAWBATCHORDER 18
#define ONRSPSTOCKCALCABLEENTRUSTQTY 19
#define ONRSPSTOCKCALCABLEPURCHASEETFQTY 20
#define ONRSPSTOCKQRYFREEZEFUNDSDETAIL 21
#define ONRSPSTOCKQRYFREEZESTOCKDETAIL 22
#define ONRSPSTOCKQRYTRANSFERSTOCKDETAIL 23
#define ONRSPSTOCKQRYTRANSFERFUNDSDETAIL 24
#define ONRSPSTOCKQRYSTOCKINFO 25
#define ONRSPSTOCKQRYSTOCKSTATICINFO 26
#define ONRSPSTOCKQRYTRADETIME 27
#define ONSTOCKENTRUSTORDERRTN 28
#define ONSTOCKTRADERTN 29
#define ONSTOCKWITHDRAWORDERRTN 30
#define ONRSPSOPUSERLOGIN 31
#define ONRSPSOPUSERLOGOUT 32
#define ONRSPSOPUSERPASSWORDUPDATE 33
#define ONRSPSOPENTRUSTORDER 34
#define ONRSPSOPQUOTEENTRUSTORDER 35
#define ONRSPSOPGROUPSPLIT 36
#define ONRSPSOPGROUPEXECTUEORDER 37
#define ONRSPSOPQRYGROUPPOSITION 38
#define ONRSPSOPLOCKOUNLOCKSTOCK 39
#define ONRSPSOPWITHDRAWORDER 40
#define ONRSPSOPQRYENTRUSTORDER 41
#define ONRSPSOPQRYSERIALTRADE 42
#define ONRSPSOPQRYPOSITION 43
#define ONRSPSOPQRYCOLLATERALPOSITION 44
#define ONRSPSOPQRYCAPITALACCOUNTINFO 45
#define ONRSPSOPQRYACCOUNTINFO 46
#define ONRSPSOPQRYSHAREHOLDERINFO 47
#define ONRSPSOPCALCABLEENTRUSTQTY 48
#define ONRSPSOPQRYABLELOCKSTOCK 49
#define ONRSPSOPQRYCONTACTINFO 50
#define ONRSPSOPEXECTUEORDER 51
#define ONRSPSOPQRYEXECASSIINFO 52
#define ONRSPSOPQRYTRADETIME 53
#define ONRSPSOPQRYEXCHANGEINFO 54
#define ONRSPSOPQRYCOMMISSION 55
#define ONRSPSOPQRYDEPOSIT 56
#define ONRSPSOPQRYCONTRACTOBJECTINFO 57
#define ONSOPENTRUSTORDERRTN 58
#define ONSOPTRADERTN 59
#define ONSOPWITHDRAWORDERRTN 60
#define ONSOPQUOTEENTRUSTORDERRTN 61
#define ONRSPSOPCAPITALTRANINOUT 62
#define ONRSPSOPCAPITALDISTRIBUTIONRATIO 63
#define ONRSPSOPFUNDTRANSBETWEENNODES 64
#define ONRSPSOPMODCAPITALDISTRIBUTIONRATIO 65
#define ONRSPFASLUSERLOGIN 66
#define ONRSPFASLUSERLOGOUT 67
#define ONRSPFASLQRYABLEFININFO 68
#define ONRSPFASLQRYABLESLOINFO 69
#define ONRSPFASLTRANSFERCOLLATERAL 70
#define ONRSPFASLDIRECTREPAYMENT 71
#define ONRSPFASLREPAYSTOCKTRANSFER 72
#define ONRSPFASLENTRUSTCRDTORDER 73
#define ONRSPFASLENTRUSTORDER 74
#define ONRSPFASLCALCABLEENTRUSTCRDTQTY 75
#define ONRSPFASLQRYCRDTFUNDS 76
#define ONRSPFASLQRYCRDTCONTRACT 77
#define ONRSPFASLQRYCRDTCONCHANGEINFO 78
#define ONRSPFASLTRANSFERFUNDS 79
#define ONRSPFASLTRANSFERSTOCK 80
#define ONRSPFASLQRYACCOUNTINFO 81
#define ONRSPFASLQRYCAPITALACCOUNTINFO 82
#define ONRSPFASLQRYSHAREHOLDERINFO 83
#define ONRSPFASLQRYPOSITION 84
#define ONRSPFASLQRYENTRUSTORDER 85
#define ONRSPFASLQRYSERIALTRADE 86
#define ONRSPFASLQRYREALTIMETRADE 87
#define ONRSPFASLQRYFREEZEFUNDSDETAIL 88
#define ONRSPFASLQRYFREEZESTOCKDETAIL 89
#define ONRSPFASLQRYTRANSFERFUNDSDETAIL 90
#define ONRSPFASLWITHDRAWORDER 91
#define ONRSPFASLQRYSYSTEMTIME 92
#define ONRSPFASLQRYTRANSFERREDCONTRACT 93
#define ONRSPFASLDESIRABLEFUNDSOUT 94
#define ONRSPFASLQRYGUARANTEEDCONTRACT 95
#define ONRSPFASLQRYUNDERLYINGCONTRACT 96
#define ONRSPFASLQRYCENTREFUNDAVLINFO 97
#define ONRSPFASLQRYPLACINGINTERESTSINFO 98
#define ONRSPFASLUSERPASSWORDUPDATE 99
#define ONFASLENTRUSTORDERRTN 100
#define ONFASLTRADERTN 101
#define ONFASLWITHDRAWORDERRTN 102
#define ONFASLLIABILITIESRTN 103
#define ONRSPSTOCKETFENTRUSTORDER 104
#define ONRSPSTOCKETFBASKETORDER 105
#define ONRSPSTOCKBONDREPURCHASEORDER 106
#define ONRSPSTOCKBONDINOUTSTOCKORDER 107
#define ONRSPSTOCKISSUEBUSINESSORDER 108
#define ONRSPSTOCKLOFENTRUSTORDER 109
#define ONRSPSTOCKAFTERHOURSPRICEORDER 110
#define ONRSPSTOCKNONTRADINGBUSINESSORDER 111
#define ONRSPSTOCKSHMUTUALFUNDORDER 112
#define ONRSPSTOCKCALCABLEPURCHASEETFBASKETQTY 113
#define ONRSPSTOCKCALCABLEBONDREPURCHASEQTY 114
#define ONRSPSTOCKCALCABLEISSUEBUSINESSQTY 115
#define ONRSPSTOCKCALCABLEPURCHASELOFQTY 116
#define ONRSPSTOCKCALCABLEAFTERHOURSPRICEQTY 117
#define ONRSPSTOCKCALCABLENONTRADINGBUSINESSQTY 118
#define ONRSPSTOCKCALCABLESHMUTUALFUNDQTY 119


///-------------------------------------------------------------------------------------
///C++ SPI�Ļص���������ʵ��
///-------------------------------------------------------------------------------------

//API�ļ̳�ʵ��

class TdApi : public DFITCSECTraderSpi
{
private:
	DFITCSECTraderApi* api;            //API����
	thread task_thread;                    //�����߳�ָ�루��python���������ݣ�
	TaskQueue task_queue;                //�������
	bool active = false;                //����״̬
public:
	TdApi()
	{
	};

	~TdApi()
	{
		if (this->active)
		{
			this->exit();
		}
	};
	//-------------------------------------------------------------------------------------
	//API�ص�����
	//-------------------------------------------------------------------------------------

	/**
	 * SEC-��������������Ӧ
	 */
	virtual void OnFrontConnected();
	/**
	 * SEC-�������Ӳ�������Ӧ
	 */
	virtual void OnFrontDisconnected(int nReason);
	/**
	 * SEC-��Ϣ֪ͨ
	 */
	virtual void OnRtnNotice(DFITCSECRspNoticeField *pNotice);
	/**
	* ERR-����Ӧ��
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ַ
	*/
	virtual void OnRspError(DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-��¼��Ӧ
	* @param pData:ָ�����ǿ�,�����û���¼��Ӧ��Ϣ�ṹ��ĵ�ַ,������¼����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ��������¼����ʧ��
	*/
	virtual void OnRspStockUserLogin(DFITCSECRspUserLoginField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-�ǳ���Ӧ
	* @param pData:ָ�����ǿ�,�����û��ǳ���Ӧ��Ϣ�ṹ��ĵ�ַ,�����ǳ�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ǳ�����ʧ��
	*/
	virtual void OnRspStockUserLogout(DFITCSECRspUserLogoutField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-���������Ӧ
	* @param pData:ָ�����ǿ�,�����û����������Ӧ��Ϣ�ṹ��ĵ�ַ,���������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������������ʧ��
	*/
	virtual void OnRspStockUserPasswordUpdate(DFITCSECRspPasswordUpdateField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-ί�б�����Ӧ
	* @param pData:ָ�����ǿ�,�����û�ί�б�����Ӧ��Ϣ�ṹ��ĵ�ַ,������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ί�б�������ʧ��
	*/
	virtual void OnRspStockEntrustOrder(DFITCStockRspEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-ί�г�����Ӧ
	* @param pData:ָ�����ǿ�,�����û�ί�г�����Ӧ��Ϣ�ṹ��ĵ�ַ,������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ί�г�������ʧ��
	*/
	virtual void OnRspStockWithdrawOrder(DFITCSECRspWithdrawOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-ί�в�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�ί�в�ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,������ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ί�в�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryEntrustOrder(DFITCStockRspQryEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-ʵʱ�ɽ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�ʵʱ�ɽ���ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,����ʵʱ�ɽ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ʵʱ�ɽ���ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryRealTimeTrade(DFITCStockRspQryRealTimeTradeField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�ֱʳɽ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֱʳɽ���ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,�����ֱʳɽ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ֱʳɽ���ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQrySerialTrade(DFITCStockRspQrySerialTradeField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�ֲֲ�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֲֲ�ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,�����ֲֲ�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ֲֲ�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryPosition(DFITCStockRspQryPositionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�ʽ��˺Ų�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ʽ��˺Ų�ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,�����ʽ��˺Ų�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ʽ��˺Ų�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryCapitalAccountInfo(DFITCStockRspQryCapitalAccountField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�����˺Ų�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û������˺Ų�ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,���������˺Ų�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������˺Ų�ѯ����ʧ��
	*/
	virtual void OnRspStockQryAccountInfo(DFITCStockRspQryAccountField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-�ɶ��Ų�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ɶ��Ų�ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,�����ɶ��Ų�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ɶ��Ų�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryShareholderInfo(DFITCStockRspQryShareholderField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�ʽ������Ӧ
	* @param pData:ָ�����ǿ�,�����û��ʽ������Ӧ��Ϣ�ṹ��ĵ�ַ,�������ʽ��������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ʽ��������ʧ��
	*/
	virtual void OnRspStockTransferFunds(DFITCStockRspTransferFundsField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-����ί����Ӧ
	* @param pData:ָ�����ǿ�,�����û�����ί����Ӧ��Ϣ�ṹ��ĵ�ַ,��������ί������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������ί������ʧ��
	*/
	virtual void OnRspStockEntrustBatchOrder(DFITCStockRspEntrustBatchOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-����������Ӧ
	* @param pData:ָ�����ǿ�,�����û�����������Ӧ��Ϣ�ṹ��ĵ�ַ,����������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������������������ʧ��
	*/
	virtual void OnRspStockWithdrawBatchOrder(DFITCStockRspWithdrawBatchOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-�����ί��������Ӧ
	* @param pData:ָ�����ǿ�,�����û������ί��������Ӧ��Ϣ�ṹ��ĵ�ַ,���������ί����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������ί����������ʧ��
	*/
	virtual void OnRspStockCalcAbleEntrustQty(DFITCStockRspCalcAbleEntrustQtyField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-�����깺ETF������Ӧ
	* @param pData:ָ�����ǿ�,�����û������깺ETF������Ӧ��Ϣ�ṹ��ĵ�ַ,���������깺ETF��������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������깺ETF��������ʧ��
	*/
	virtual void OnRspStockCalcAblePurchaseETFQty(DFITCStockRspCalcAblePurchaseETFQtyField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-�����ʽ���ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û������ʽ���ϸ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,���������ʽ���ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������ʽ���ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryFreezeFundsDetail(DFITCStockRspQryFreezeFundsDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-����֤ȯ��ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�����֤ȯ��ϸ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,��������֤ȯ��ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������֤ȯ��ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryFreezeStockDetail(DFITCStockRspQryFreezeStockDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-����֤ȯ��ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�����֤ȯ��ϸ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,��������֤ȯ��ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������֤ȯ��ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryTransferStockDetail(DFITCStockRspQryTransferStockDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-�����ʽ���ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û������ʽ���ϸ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,���������ʽ���ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������ʽ���ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryTransferFundsDetail(DFITCStockRspQryTransferFundsDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-֤ȯ��Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�֤ȯ��Ϣ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,����֤ȯ��Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������֤ȯ��Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryStockInfo(DFITCStockRspQryStockField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-֤ȯ��̬��Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�֤ȯ��̬��Ϣ��ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,����֤ȯ��̬��Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������֤ȯ��̬��Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockQryStockStaticInfo(DFITCStockRspQryStockStaticField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* STOCK-����ʱ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�����ʱ���ѯ��Ӧ��Ϣ�ṹ��ĵ�ַ,��������ʱ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������ʱ���ѯ����ʧ��
	*/
	virtual void OnRspStockQryTradeTime(DFITCStockRspQryTradeTimeField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* STOCK-ί�лر���Ӧ
	* @param pData:����ί�лر��ṹ��ĵ�ַ
	*/
	virtual void OnStockEntrustOrderRtn(DFITCStockEntrustOrderRtnField * pData);
	/**
	* STOCK-�ɽ��ر���Ӧ
	* @param pData:���سɽ��ر��ṹ��ĵ�ַ
	*/
	virtual void OnStockTradeRtn(DFITCStockTradeRtnField * pData);
	/**
	* STOCK-�����ر���Ӧ
	* @param pData:���س����ر��ṹ��ĵ�ַ
	*/
	virtual void OnStockWithdrawOrderRtn(DFITCStockWithdrawOrderRtnField * pData);

	/**
	* SOP-��¼��Ӧ
	* @param pRspUserLogin:ָ�����ǿ�,�����û���¼��Ӧ��Ϣ�ṹ��ַ,������¼����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������¼����ʧ��
	*/
	virtual void OnRspSOPUserLogin(DFITCSECRspUserLoginField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	 * SOP-�ǳ���Ӧ
	 * @param pData:ָ�����ǿ�,�����û��ǳ���Ӧ��Ϣ�ṹ��ַ,�����ǳ�����ɹ�
	 * @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ǳ�����ʧ��
	 */
	virtual void OnRspSOPUserLogout(DFITCSECRspUserLogoutField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�û����������Ӧ
	* @param pData:ָ�����ǿ�,�����û����������Ӧ��Ϣ�ṹ��ַ,�����û������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������û������������ʧ��
	*/
	virtual void OnRspSOPUserPasswordUpdate(DFITCSECRspPasswordUpdateField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-������Ӧ
	* @param pData:ָ�����ǿ�,�����û�������Ӧ��Ϣ�ṹ��ַ,������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������������ʧ��
	*/
	virtual void OnRspSOPEntrustOrder(DFITCSOPRspEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�����̱�����Ӧ
	* @param pData:ָ�����ǿ�,�����û�����ί����Ӧ��Ϣ�ṹ��ַ,���������̱�������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�����������̱�������ʧ��
	*/
	virtual void OnRspSOPQuoteEntrustOrder(DFITCSOPRspQuoteEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-��ϲ��ί����Ӧ
	* @param pData:ָ�����ǿ�,�����û���ϲ��ί����Ӧ��Ϣ�ṹ��ַ,������ϲ��ί������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������ϲ��ί������ʧ��
	*/
	virtual void OnRspSOPGroupSplit(DFITCSOPRspEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	 * SOP-��Ȩ�����Ȩί����Ӧ
	 * @param pData:ָ�����ǿ�,�����û���Ȩ�����Ȩί����Ӧ��Ϣ�ṹ��ַ,������Ȩ�����Ȩί������ɹ�
	 * @return pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������Ȩ�����Ȩί������ʧ�ܣ�������������error.xml
	 */
	virtual void OnRspSOPGroupExectueOrder(DFITCSOPRspGroupExectueOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-��ѯ�ͻ���ϳֲ���ϸ��Ӧ
	* @param pData:ָ�����ǿ�,�����û���ѯ�ͻ���ϳֲ���ϸ��Ӧ�ṹ��ַ,������ѯ�ͻ���ϳֲ���ϸ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������ѯ�ͻ���ϳֲ���ϸ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryGroupPosition(DFITCSOPRspQryGroupPositionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-֤ȯ����������Ӧ
	* @param pData:ָ�����ǿ�,�����û�֤ȯ����������Ӧ��Ϣ�ṹ��ַ,����֤ȯ������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ������֤ȯ������������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPLockOUnLockStock(DFITCSOPRspLockOUnLockStockField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-������Ӧ
	* @param pData:ָ�����ǿ�,�����û�������Ӧ��Ϣ�ṹ��ַ,������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������������ʧ��
	*/
	virtual void OnRspSOPWithdrawOrder(DFITCSECRspWithdrawOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-ί�в�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�ί�в�ѯ��Ӧ��Ϣ�ṹ��ַ,����ί�в�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ������ί�в�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryEntrustOrder(DFITCSOPRspQryEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-�ֱʳɽ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֱʳɽ���ѯ��Ӧ��Ϣ�ṹ��ַ,�����ֱʳɽ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ֱʳɽ���ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQrySerialTrade(DFITCSOPRspQrySerialTradeField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-�ֲֲ�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֲֲ�ѯ��Ӧ��Ϣ�ṹ��ַ,�����ֲֲ�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ֲֲ�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryPosition(DFITCSOPRspQryPositionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-�ͻ������ֲֲ�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ������ֲֲ�ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ������ֲֲ�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ������ֲֲ�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryCollateralPosition(DFITCSOPRspQryCollateralPositionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-�ͻ��ʽ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ��ʽ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ��ʽ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ��ʽ��ѯ����ʧ��
	*/
	virtual void OnRspSOPQryCapitalAccountInfo(DFITCSOPRspQryCapitalAccountField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�ͻ���Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ���Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ���Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ���Ϣ��ѯ����ʧ��
	*/
	virtual void OnRspSOPQryAccountInfo(DFITCSOPRspQryAccountField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�ɶ���Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ɶ���Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ɶ���Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ɶ���Ϣ��ѯ����ʧ��
	*/
	virtual void OnRspSOPQryShareholderInfo(DFITCSOPRspQryShareholderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-��ί��������ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û���ί��������ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ���ί��������ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ί��������ѯ����ʧ��
	*/
	virtual void OnRspSOPCalcAbleEntrustQty(DFITCSOPRspCalcAbleEntrustQtyField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�ͻ�������֤ȯ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ�������֤ȯ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ�������֤ȯ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ�������֤ȯ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryAbleLockStock(DFITCSOPRspQryAbleLockStockField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��Ȩ��Լ�����ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û���Ȩ��Լ�����ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ���Ȩ��Լ�����ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���Ȩ��Լ�����ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryContactInfo(DFITCSOPRspQryContactField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-ִ��ί����Ӧ
	* @param pData:ָ�����ǿ�,�����û�ִ��ί����Ӧ��Ϣ�ṹ��ַ,�����ͻ�ִ��ί������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�ִ��ί������ʧ��
	*/
	virtual void OnRspSOPExectueOrder(DFITCSOPRspExectueOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* SOP-�ͻ���Ȩָ����Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ���Ȩָ����Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ���Ȩָ����Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ���Ȩָ����Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryExecAssiInfo(DFITCSOPRspQryExecAssiInfoField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��ѯ����ʱ����Ӧ
	* @param pData:ָ�����ǿ�,�����û���ѯ����ʱ����Ӧ��Ϣ�ṹ��ַ,�����ͻ���ѯ����ʱ������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ѯ����ʱ������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryTradeTime(DFITCSOPRspQryTradeTimeField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��ȡ���н�����������Ӧ
	* @param pData:ָ�����ǿ�,�����û���ȡ���н�����������Ӧ��Ϣ�ṹ��ַ,�����ͻ���ȡ���н�������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ȡ���н�������������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryExchangeInfo(DFITCSOPRspQryExchangeInfoField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��ѯ�����Ѳ�����Ӧ
	* @param pData:ָ�����ǿ�,�����û���ѯ�����Ѳ�����Ӧ��Ϣ�ṹ��ַ,�����ͻ���ѯ�����Ѳ�������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ѯ�����Ѳ�������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryCommission(DFITCSOPRspQryCommissionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��ѯ��֤���ʲ�����Ӧ
	* @param pData:ָ�����ǿ�,�����û���ѯ��֤���ʲ�����Ӧ��Ϣ�ṹ��ַ,�����ͻ���ѯ��֤���ʲ�������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ѯ��֤���ʲ�������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryDeposit(DFITCSOPRspQryDepositField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-��Ȩ�����Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û���Ȩ�����Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ���Ȩ�����Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���Ȩ�����Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPQryContractObjectInfo(DFITCSOPRspQryContractObjectField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* SOP-ί�лر���Ӧ
	* @param pData:����ί�лر��ṹ��ĵ�ַ
	*/
	virtual void OnSOPEntrustOrderRtn(DFITCSOPEntrustOrderRtnField * pData);
	/**
	* SOP-�ɽ��ر���Ӧ
	* @param pData:���سɽ��ر��ṹ��ĵ�ַ
	*/
	virtual void OnSOPTradeRtn(DFITCSOPTradeRtnField * pData);
	/**
	* SOP-�����ر���Ӧ
	* @param pData:���س����ر��ṹ��ĵ�ַ
	*/
	virtual void OnSOPWithdrawOrderRtn(DFITCSOPWithdrawOrderRtnField * pData);
	/**
	* SOP-����ί�лر���Ӧ
	* @param pData:��������˫�߱���ί�лر��ṹ��ĵ�ַ
	*/
	virtual void OnSOPQuoteEntrustOrderRtn(DFITCSOPQuoteEntrustOrderRtnField * pData);

	/**
	* SOP-�ʽ���������Ӧ
	* @param pData:ָ�����ǿ�,�����ʽ���������Ӧ��Ϣ�ṹ��ַ,�����ͻ��ʽ�����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ʽ�����������ʧ��
	*/
	virtual void OnRspSOPCapitalTranInOut(DFITCSOPRspCapitalTranInOutField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* SOP-�ʽ��ڵ���������ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����ʽ��ڵ���������Ӧ��Ϣ�ṹ��ַ,�����ͻ��ʽ��ڵ������������ѯ�ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ʽ��ڵ���������ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspSOPCapitalDistributionRatio(DFITCSOPRspQryCapitalDistributionRatioField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);

	/**
	* SOP-�ڵ���ʽ𻮲���Ӧ
	* @param pData:ָ�����ǿ�,���ؽڵ���ʽ𻮲���Ӧ��Ϣ�ṹ��ַ,�����ͻ��ڵ���ʽ𻮲�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ڵ���ʽ𻮲�����ʧ��
	*/
	virtual void OnRspSOPFundTransBetweenNodes(DFITCSOPRspFundTransBetweenNodesField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* SOP-�޸��ʽ��ڵ���������Ӧ
	* @param pData:ָ�����ǿ�,���������ʽ��ڵ���������Ӧ��Ϣ�ṹ��ַ,�������ÿͻ��ʽ��ڵ�����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�����������ʽ��ڵ�����������ʧ��
	*/
	virtual void OnRspSOPModCapitalDistributionRatio(DFITCSOPRspModCapitalDistributionRatioField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* FASL-��¼��Ӧ
	* @param pData:ָ�����ǿ�,�����û�������ȯ��¼��Ӧ��Ϣ�ṹ��ַ,�����ͻ�������ȯ��¼����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�������ȯ��¼����ʧ��
	*/
	virtual void OnRspFASLUserLogin(DFITCSECRspUserLoginField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-�ǳ���Ӧ
	* @param pData:ָ�����ǿ�,�����û�������ȯ�ǳ���Ӧ��Ϣ�ṹ��ַ,�����ͻ�������ȯ�ǳ�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�������ȯ�ǳ�����ʧ��
	*/
	virtual void OnRspFASLUserLogout(DFITCSECRspUserLogoutField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-�ͻ���������Ϣ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ���������Ϣ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ���������Ϣ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ���������Ϣ����ʧ��
	*/
	virtual void OnRspFASLQryAbleFinInfo(DFITCFASLRspAbleFinInfoField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-�ͻ�����ȯ��Ϣ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ�����ȯ��Ϣ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ�����ȯ��Ϣ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ�����ȯ��Ϣ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryAbleSloInfo(DFITCFASLRspAbleSloInfoField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�����ﻮת��Ӧ
	* @param pData:ָ�����ǿ�,�����û������ﻮת��Ӧ��Ϣ�ṹ��ַ,�����ͻ������ﻮת����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ������ﻮת����ʧ��
	*/
	virtual void OnRspFASLTransferCollateral(DFITCFASLRspTransferCollateralField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-ֱ�ӻ�����Ӧ
	* @param pData:ָ�����ǿ�,�����û�ֱ�ӻ�����Ӧ��Ϣ�ṹ��ַ,�����ͻ�ֱ�ӻ�������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�ֱ�ӻ�������ʧ��
	*/
	virtual void OnRspFASLDirectRepayment(DFITCFASLRspDirectRepaymentField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-��ȯ��ת��Ӧ
	* @param pData:ָ�����ǿ�,�����û���ȯ��ת��Ӧ��Ϣ�ṹ��ַ,�����ͻ���ȯ��ת����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ȯ��ת����ʧ��
	*/
	virtual void OnRspFASLRepayStockTransfer(DFITCFASLRspRepayStockTransferField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-���ý�����Ӧ
	* @param pData:ָ�����ǿ�,�����û����ý�����Ӧ��Ϣ�ṹ��ַ,�����ͻ����ý�������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ����ý�������ʧ��
	*/
	virtual void OnRspFASLEntrustCrdtOrder(DFITCFASLRspEntrustCrdtOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-������ȯ������Ӧ
	* @param pData:ָ�����ǿ�,�����û�������ȯ������Ӧ��Ϣ�ṹ��ַ,�����ͻ�������ȯ��������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�������ȯ��������ʧ��
	*/
	virtual void OnRspFASLEntrustOrder(DFITCFASLRspEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-���ÿ�ί��������ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û����ÿ�ί��������ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ����ÿ�ί��������ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ����ÿ�ί��������ѯ����ʧ��
	*/
	virtual void OnRspFASLCalcAbleEntrustCrdtQty(DFITCFASLRspCalcAbleEntrustCrdtQtyField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-��ѯ�����ʽ���Ӧ
	* @param pData:ָ�����ǿ�,�����û���ѯ�����ʽ���Ӧ��Ϣ�ṹ��ַ,�����ͻ���ѯ�����ʽ�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ѯ�����ʽ�����ʧ��
	  * @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryCrdtFunds(DFITCFASLRspQryCrdtFundsField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-���ú�Լ��Ϣ��Ӧ
	* @param pData:ָ�����ǿ�,�����û����ú�Լ��Ϣ��Ӧ��Ϣ�ṹ��ַ,�����ͻ����ú�Լ��Ϣ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ����ú�Լ��Ϣ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryCrdtContract(DFITCFASLRspQryCrdtContractField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLat);
	/**
	* FASL-���ú�Լ�䶯��Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û����ú�Լ�䶯��Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ����ú�Լ�䶯��Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ����ú�Լ�䶯��Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryCrdtConChangeInfo(DFITCFASLRspQryCrdtConChangeInfoField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ʽ��ת��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ʽ��ת��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ʽ��ת����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ʽ��ת����ʧ��
	*/
	virtual void OnRspFASLTransferFunds(DFITCFASLRspTransferFundsField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-֤ȯ��ת��Ӧ
	* @param pData:ָ�����ǿ�,�����û�֤ȯ��ת��Ӧ��Ϣ�ṹ��ַ,�����ͻ�֤ȯ��ת����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�֤ȯ��ת����ʧ��
	*/
	virtual void OnRspFASLTransferStock(DFITCFASLRspTransferStockField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-�ͻ���Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ���Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ���Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ���Ϣ��ѯ����ʧ��
	*/
	virtual void OnRspFASLQryAccountInfo(DFITCFASLRspQryAccountField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-�ͻ��ʽ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ͻ��ʽ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ͻ��ʽ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ͻ��ʽ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryCapitalAccountInfo(DFITCFASLRspQryCapitalAccountField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ɶ���Ϣ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ɶ���Ϣ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ɶ���Ϣ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ɶ���Ϣ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryShareholderInfo(DFITCFASLRspQryShareholderField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ֲֲ�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֲֲ�ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ֲֲ�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ֲֲ�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryPosition(DFITCFASLRspQryPositionField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-ί�в�ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�ί�в�ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ�ί�в�ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�ί�в�ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryEntrustOrder(DFITCFASLRspQryEntrustOrderField * pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ֱʳɽ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ֱʳɽ���ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ֱʳɽ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ֱʳɽ���ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQrySerialTrade(DFITCFASLRspQrySerialTradeField * pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-ʵʱ�ɽ���ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�ʵʱ�ɽ���ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ�ʵʱ�ɽ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�ʵʱ�ɽ���ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryRealTimeTrade(DFITCFASLRspQryRealTimeTradeField * pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ʽ𶳽���ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ʽ𶳽���ϸ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ʽ𶳽���ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ʽ𶳽���ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryFreezeFundsDetail(DFITCFASLRspQryFreezeFundsDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-֤ȯ������ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û�֤ȯ������ϸ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ�֤ȯ������ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ�֤ȯ������ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryFreezeStockDetail(DFITCFASLRspQryFreezeStockDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ʽ������ϸ��ѯ��Ӧ
	* @param pData:ָ�����ǿ�,�����û��ʽ������ϸ��ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ��ʽ������ϸ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ��ʽ������ϸ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryTransferFundsDetail(DFITCFASLRspQryTransferFundsDetailField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-������Ӧ
	* @param pData:ָ�����ǿ�,�����û�������Ӧ��Ϣ�ṹ��ַ,������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������������ʧ��
	*/
	virtual void OnRspFASLWithdrawOrder(DFITCFASLRspWithdrawOrderField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-��ǰϵͳʱ���ѯ������Ӧ
	* @param pData:ָ�����ǿ�,�����û�ϵͳʱ���ѯ��Ӧ��Ϣ�ṹ��ַ,����ϵͳʱ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ������ϵͳʱ���ѯ����ʧ��
	*/
	virtual void OnRspFASLQrySystemTime(DFITCFASLRspQryTradeTimeField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-��ת�뵣��֤ȯ��ѯ������Ӧ
	* @param pData:ָ�����ǿ�,���ؿ�ת�뵣��֤ȯ��ѯ��Ӧ��Ϣ�ṹ��ַ,������ת�뵣��֤ȯ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ��������ת�뵣��֤ȯ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryTransferredContract(DFITCFASLRspQryTransferredContractField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ͻ���ȡ�ʽ����������Ӧ
	* @param pData:ָ�����ǿ�,���ؿͻ���ȡ�ʽ������Ӧ��Ϣ�ṹ��ַ,�����ͻ���ȡ�ʽ��������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ�������ͻ���ȡ�ʽ��������ʧ��
	*/
	virtual void OnRspFASLDesirableFundsOut(DFITCFASLRspDesirableFundsOutField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-����֤ȯ��ѯ������Ӧ
	* @param pData:ָ�����ǿ�,���ص���֤ȯ��ѯ��Ӧ��Ϣ�ṹ��ַ,��������֤ȯ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ����������֤ȯ��ѯ����ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryGuaranteedContract(DFITCFASLRspQryGuaranteedContractField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-���֤ȯ��ѯ������Ӧ
	* @param pData:ָ�����ǿ�,���ر��֤ȯ��ѯ��Ӧ��Ϣ�ṹ��ַ,�������֤ȯ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ���������֤ȯ��ѯʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryUnderlyingContract(DFITCFASLRspQryUnderlyingContractField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-���н����ʽ��ѯ������Ӧ
	* @param pData:ָ�����ǿ�,���ؼ��н����ʽ��ѯ��Ӧ��Ϣ�ṹ��ַ,�������н����ʽ��ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ���������֤ȯ��ѯʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryCentreFundAvlInfo(DFITCFASLRspQryCentreFundAvlField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-�ͻ�����Ȩ���ѯ������Ӧ
	* @param pData:ָ�����ǿ�,���ؿͻ�����Ȩ���ѯ��Ӧ��Ϣ�ṹ��ַ,�����ͻ�����Ȩ���ѯ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ��ַ���������֤ȯ��ѯʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspFASLQryPlacingInterestsInfo(DFITCFASLRspQryPlacingInterestsField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);
	/**
	* FASL-���������Ӧ
	* @param pData:ָ�����ǿ�,�����û����������Ӧ��Ϣ�ṹ��ĵ�ַ,���������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������������ʧ��
	*/
	virtual void OnRspFASLUserPasswordUpdate(DFITCSECRspPasswordUpdateField *pData, DFITCSECRspInfoField *pRspInfo);
	/**
	* FASL-ί�лر���Ӧ
	* @param pData:����ί�лر��ṹ��ĵ�ַ
	*/
	virtual void OnFASLEntrustOrderRtn(DFITCFaslEntrustOrderRtnField *pData);
	/**
	* FASL-�ɽ��ر���Ӧ
	* @param pData:���سɽ��ر��ṹ��ĵ�ַ
	*/
	virtual void OnFASLTradeRtn(DFITCFaslTradeRtnField *pData);
	/**
	* FASL-�����ر���Ӧ
	* @param pData:���س����ر��ṹ��ĵ�ַ
	*/
	virtual void OnFASLWithdrawOrderRtn(DFITCFaslWithdrawOrderRtnField *pData);
	/**
	* FASL-��ծ�䶯��Ӧ
	* @param pData:���ظ�ծ�䶯�ṹ��ĵ�ַ
	*/
	virtual void OnFASLLiabilitiesRtn(DFITCFaslLiabilitiesRtnField *pData);

	//����ΪSTOCK����ҵ�����Ӧ�ӿ�
	/**
	* STOCK-ETF����ί����Ӧ
	* @param pData:ָ�����ǿ�,����ETF����ί����Ӧ��Ϣ�ṹ��ĵ�ַ,����ETF����ί������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ETF����ί������ʧ��
	*/
	virtual void OnRspStockETFEntrustOrder(DFITCStockRspETFEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-ETF���ӹ�������Ӧ
	* @param pData:ָ�����ǿ�,����ETF���ӹ�������Ӧ��Ϣ�ṹ��ĵ�ַ,����ETF���ӹ���������ɹ�,pData->localOrderIDС��0˵���óɷֹ�����ʧ�ܡ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ETF���ӹ���������ʧ��
	* @param bIsLast:����ֵ�����Ƿ������һ����Ӧ��Ϣ(0-��,1-��)
	*/
	virtual void OnRspStockETFBasketOrder(DFITCStockRspETFBasketOrderField *pData, DFITCSECRspInfoField *pRspInfo, bool bIsLast);

	/**
	* STOCK-ծȯ�ع���Ӧ
	* @param pData:ָ�����ǿ�,����ծȯ�ع���Ӧ��Ϣ�ṹ��ĵ�ַ,����ծȯ�ع�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ծȯ�ع�����ʧ��
	*/
	virtual void OnRspStockBondRepurchaseOrder(DFITCStockRspBondRepurchaseOrderField *pData, DFITCSECRspInfoField *pRspInfo);


	/**
	* STOCK-ծȯ�������Ӧ
	* @param pData:ָ�����ǿ�,����ծȯ�������Ӧ��Ϣ�ṹ��ĵ�ַ,����ծȯ���������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������ί�б�������ʧ��
	*/
	virtual void OnRspStockBondInOutStockOrder(DFITCStockRspBondInOutStockOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-����ҵ����Ӧ
	* @param pData:ָ�����ǿ�,���ط���ҵ����Ӧ��Ϣ�ṹ��ĵ�ַ,��������ҵ������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������ҵ������ʧ��
	*/
	virtual void OnRspStockIssueBusinessOrder(DFITCStockRspIssueBusinessOrderField *pData, DFITCSECRspInfoField *pRspInfo);


	/**
	* STOCK-LOF������Ӧ
	* @param pData:ָ�����ǿ�,����LOF������Ӧ��Ϣ�ṹ��ĵ�ַ,����LOF��������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ������LOF��������ʧ��
	*/
	virtual void OnRspStockLOFEntrustOrder(DFITCStockRspLOFEntrustOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-�̺󶨼���Ӧ
	* @param pData:ָ�����ǿ�,�����̺󶨼���Ӧ��Ϣ�ṹ��ĵ�ַ,�����̺󶨼�����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������̺󶨼�����ʧ��
	*/
	virtual void OnRspStockAfterHoursPriceOrder(DFITCStockRspAfterHoursPriceOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-�ǽ���ҵ����Ӧ
	* @param pData:ָ�����ǿ�,���طǽ���ҵ����Ӧ��Ϣ�ṹ��ĵ�ַ,�����ǽ���ҵ������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������ǽ���ҵ������ʧ��
	*/
	virtual void OnRspStockNonTradingBusinessOrder(DFITCStockRspNonTradingBusinessOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-�Ϻ�����ͨ��Ӧ
	* @param pData:ָ�����ǿ�,�����Ϻ�����ͨ��Ӧ��Ϣ�ṹ��ĵ�ַ,�����Ϻ�����ͨ����ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�������Ϻ�����ͨʧ��
	*/
	virtual void OnRspStockSHMutualFundOrder(DFITCStockRspSHMutualFundOrderField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-���������ETF��Ʊ��������Ӧ
	* @param pData:ָ�����ǿ�,�����û����������ETF��Ʊ��������Ӧ��Ϣ�ṹ��ĵ�ַ,�������������ETF��Ʊ����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ���������������ETF��Ʊ����������ʧ��
	*/
	virtual void OnRspStockCalcAblePurchaseETFBasketQty(DFITCStockRspCalcAblePurchaseETFBasketQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-����ծȯ�ع���ί��������Ӧ
	* @param pData:ָ�����ǿ�,�����û�����ծȯ�ع���ί��������Ӧ��Ϣ�ṹ��ĵ�ַ,��������ծȯ�ع���ί����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������ծȯ�ع���ί����������ʧ��
	*/
	virtual void OnRspStockCalcAbleBondRepurchaseQty(DFITCStockRspCalcAbleBondRepurchaseQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-���㷢��ҵ����Ϲ�������Ӧ
	* @param pData:ָ�����ǿ�,�����û����㷢��ҵ����Ϲ�������Ӧ��Ϣ�ṹ��ĵ�ַ,�������㷢��ҵ����Ϲ���������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ���������㷢��ҵ����Ϲ���������ʧ��
	*/
	virtual void OnRspStockCalcAbleIssueBusinessQty(DFITCStockRspCalcAbleIssueBusinessQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-����LOFҵ���ί��������Ӧ
	* @param pData:ָ�����ǿ�,�����û�����LOFҵ���ί��������Ӧ��Ϣ�ṹ��ĵ�ַ,��������LOFҵ���ί����������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������LOFҵ���ί����������ʧ��
	*/
	virtual void OnRspStockCalcAblePurchaseLOFQty(DFITCStockRspCalcAblePurchaseLOFQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-�����̺󶨼ۿ�����������Ӧ
	* @param pData:ָ�����ǿ�,�����û������̺󶨼ۿ���������Ӧ��Ϣ�ṹ��ĵ�ַ,���������̺󶨼ۿ�������������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������̺󶨼ۿ�������������ʧ��
	*/
	virtual void OnRspStockCalcAbleAfterHoursPriceQty(DFITCStockRspCalcAbleAfterHoursPriceQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-����ǽ���ҵ����Ϲ�������Ӧ
	* @param pData:ָ�����ǿ�,�����û�����ǽ���ҵ����Ϲ�������Ӧ��Ϣ�ṹ��ĵ�ַ,��������ǽ���ҵ����Ϲ���������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ����������ǽ���ҵ����Ϲ���������ʧ��
	*/
	virtual void OnRspStockCalcAbleNonTradingBusinessQty(DFITCStockRspCalcAbleNonTradingBusinessQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	/**
	* STOCK-�����Ϻ�����ҵ����Ϲ�������Ӧ
	* @param pData:ָ�����ǿ�,�����û������Ϻ�����ҵ����Ϲ�������Ӧ��Ϣ�ṹ��ĵ�ַ,���������Ϻ�����ҵ����Ϲ���������ɹ�
	* @param pRspInfo:ָ�����ǿգ����ش�����Ϣ�ṹ��ĵ�ַ�����������Ϻ�����ҵ����Ϲ���������ʧ��
	*/
	virtual void OnRspStockCalcAbleSHMutualFundQty(DFITCStockRspCalcAbleSHMutualFundQtyField *pData, DFITCSECRspInfoField *pRspInfo);

	//-------------------------------------------------------------------------------------
	//task������
	//-------------------------------------------------------------------------------------
	void processTask();

	void processFrontConnected(Task *task);

	void processFrontDisconnected(Task *task);

	void processRtnNotice(Task *task);

	void processRspError(Task *task);

	void processRspStockUserLogin(Task *task);

	void processRspStockUserLogout(Task *task);

	void processRspStockUserPasswordUpdate(Task *task);

	void processRspStockEntrustOrder(Task *task);

	void processRspStockWithdrawOrder(Task *task);

	void processRspStockQryEntrustOrder(Task *task);

	void processRspStockQryRealTimeTrade(Task *task);

	void processRspStockQrySerialTrade(Task *task);

	void processRspStockQryPosition(Task *task);

	void processRspStockQryCapitalAccountInfo(Task *task);

	void processRspStockQryAccountInfo(Task *task);

	void processRspStockQryShareholderInfo(Task *task);

	void processRspStockTransferFunds(Task *task);

	void processRspStockEntrustBatchOrder(Task *task);

	void processRspStockWithdrawBatchOrder(Task *task);

	void processRspStockCalcAbleEntrustQty(Task *task);

	void processRspStockCalcAblePurchaseETFQty(Task *task);

	void processRspStockQryFreezeFundsDetail(Task *task);

	void processRspStockQryFreezeStockDetail(Task *task);

	void processRspStockQryTransferStockDetail(Task *task);

	void processRspStockQryTransferFundsDetail(Task *task);

	void processRspStockQryStockInfo(Task *task);

	void processRspStockQryStockStaticInfo(Task *task);

	void processRspStockQryTradeTime(Task *task);

	void processStockEntrustOrderRtn(Task *task);

	void processStockTradeRtn(Task *task);

	void processStockWithdrawOrderRtn(Task *task);

	void processRspSOPUserLogin(Task *task);

	void processRspSOPUserLogout(Task *task);

	void processRspSOPUserPasswordUpdate(Task *task);

	void processRspSOPEntrustOrder(Task *task);

	void processRspSOPQuoteEntrustOrder(Task *task);

	void processRspSOPGroupSplit(Task *task);

	void processRspSOPGroupExectueOrder(Task *task);

	void processRspSOPQryGroupPosition(Task *task);

	void processRspSOPLockOUnLockStock(Task *task);

	void processRspSOPWithdrawOrder(Task *task);

	void processRspSOPQryEntrustOrder(Task *task);

	void processRspSOPQrySerialTrade(Task *task);

	void processRspSOPQryPosition(Task *task);

	void processRspSOPQryCollateralPosition(Task *task);

	void processRspSOPQryCapitalAccountInfo(Task *task);

	void processRspSOPQryAccountInfo(Task *task);

	void processRspSOPQryShareholderInfo(Task *task);

	void processRspSOPCalcAbleEntrustQty(Task *task);

	void processRspSOPQryAbleLockStock(Task *task);

	void processRspSOPQryContactInfo(Task *task);

	void processRspSOPExectueOrder(Task *task);

	void processRspSOPQryExecAssiInfo(Task *task);

	void processRspSOPQryTradeTime(Task *task);

	void processRspSOPQryExchangeInfo(Task *task);

	void processRspSOPQryCommission(Task *task);

	void processRspSOPQryDeposit(Task *task);

	void processRspSOPQryContractObjectInfo(Task *task);

	void processSOPEntrustOrderRtn(Task *task);

	void processSOPTradeRtn(Task *task);

	void processSOPWithdrawOrderRtn(Task *task);

	void processSOPQuoteEntrustOrderRtn(Task *task);

	void processRspSOPCapitalTranInOut(Task *task);

	void processRspSOPCapitalDistributionRatio(Task *task);

	void processRspSOPFundTransBetweenNodes(Task *task);

	void processRspSOPModCapitalDistributionRatio(Task *task);

	void processRspFASLUserLogin(Task *task);

	void processRspFASLUserLogout(Task *task);

	void processRspFASLQryAbleFinInfo(Task *task);

	void processRspFASLQryAbleSloInfo(Task *task);

	void processRspFASLTransferCollateral(Task *task);

	void processRspFASLDirectRepayment(Task *task);

	void processRspFASLRepayStockTransfer(Task *task);

	void processRspFASLEntrustCrdtOrder(Task *task);

	void processRspFASLEntrustOrder(Task *task);

	void processRspFASLCalcAbleEntrustCrdtQty(Task *task);

	void processRspFASLQryCrdtFunds(Task *task);

	void processRspFASLQryCrdtContract(Task *task);

	void processRspFASLQryCrdtConChangeInfo(Task *task);

	void processRspFASLTransferFunds(Task *task);

	void processRspFASLTransferStock(Task *task);

	void processRspFASLQryAccountInfo(Task *task);

	void processRspFASLQryCapitalAccountInfo(Task *task);

	void processRspFASLQryShareholderInfo(Task *task);

	void processRspFASLQryPosition(Task *task);

	void processRspFASLQryEntrustOrder(Task *task);

	void processRspFASLQrySerialTrade(Task *task);

	void processRspFASLQryRealTimeTrade(Task *task);

	void processRspFASLQryFreezeFundsDetail(Task *task);

	void processRspFASLQryFreezeStockDetail(Task *task);

	void processRspFASLQryTransferFundsDetail(Task *task);

	void processRspFASLWithdrawOrder(Task *task);

	void processRspFASLQrySystemTime(Task *task);

	void processRspFASLQryTransferredContract(Task *task);

	void processRspFASLDesirableFundsOut(Task *task);

	void processRspFASLQryGuaranteedContract(Task *task);

	void processRspFASLQryUnderlyingContract(Task *task);

	void processRspFASLQryCentreFundAvlInfo(Task *task);

	void processRspFASLQryPlacingInterestsInfo(Task *task);

	void processRspFASLUserPasswordUpdate(Task *task);

	void processFASLEntrustOrderRtn(Task *task);

	void processFASLTradeRtn(Task *task);

	void processFASLWithdrawOrderRtn(Task *task);

	void processFASLLiabilitiesRtn(Task *task);

	void processRspStockETFEntrustOrder(Task *task);

	void processRspStockETFBasketOrder(Task *task);

	void processRspStockBondRepurchaseOrder(Task *task);

	void processRspStockBondInOutStockOrder(Task *task);

	void processRspStockIssueBusinessOrder(Task *task);

	void processRspStockLOFEntrustOrder(Task *task);

	void processRspStockAfterHoursPriceOrder(Task *task);

	void processRspStockNonTradingBusinessOrder(Task *task);

	void processRspStockSHMutualFundOrder(Task *task);

	void processRspStockCalcAblePurchaseETFBasketQty(Task *task);

	void processRspStockCalcAbleBondRepurchaseQty(Task *task);

	void processRspStockCalcAbleIssueBusinessQty(Task *task);

	void processRspStockCalcAblePurchaseLOFQty(Task *task);

	void processRspStockCalcAbleAfterHoursPriceQty(Task *task);

	void processRspStockCalcAbleNonTradingBusinessQty(Task *task);

	void processRspStockCalcAbleSHMutualFundQty(Task *task);

	//-------------------------------------------------------------------------------------
	//data���ص������������ֵ�
	//error���ص������Ĵ����ֵ�
	//id������id
	//last���Ƿ�Ϊ��󷵻�
	//i������
	//-------------------------------------------------------------------------------------

	virtual void onFrontConnected() {};

	virtual void onFrontDisconnected(int reqid) {};

	virtual void onRtnNotice(const dict &data) {};

	virtual void onRspError(const dict &error) {};

	virtual void onRspStockUserLogin(const dict &data, const dict &error) {};

	virtual void onRspStockUserLogout(const dict &data, const dict &error) {};

	virtual void onRspStockUserPasswordUpdate(const dict &data, const dict &error) {};

	virtual void onRspStockEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspStockWithdrawOrder(const dict &data, const dict &error) {};

	virtual void onRspStockQryEntrustOrder(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryRealTimeTrade(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQrySerialTrade(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryPosition(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryCapitalAccountInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryAccountInfo(const dict &data, const dict &error) {};

	virtual void onRspStockQryShareholderInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockTransferFunds(const dict &data, const dict &error) {};

	virtual void onRspStockEntrustBatchOrder(const dict &data, const dict &error) {};

	virtual void onRspStockWithdrawBatchOrder(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleEntrustQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAblePurchaseETFQty(const dict &data, const dict &error) {};

	virtual void onRspStockQryFreezeFundsDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryFreezeStockDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryTransferStockDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryTransferFundsDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryStockInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryStockStaticInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockQryTradeTime(const dict &data, const dict &error) {};

	virtual void onStockEntrustOrderRtn(const dict &data) {};

	virtual void onStockTradeRtn(const dict &data) {};

	virtual void onStockWithdrawOrderRtn(const dict &data) {};

	virtual void onRspSOPUserLogin(const dict &data, const dict &error) {};

	virtual void onRspSOPUserLogout(const dict &data, const dict &error) {};

	virtual void onRspSOPUserPasswordUpdate(const dict &data, const dict &error) {};

	virtual void onRspSOPEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspSOPQuoteEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspSOPGroupSplit(const dict &data, const dict &error) {};

	virtual void onRspSOPGroupExectueOrder(const dict &data, const dict &error) {};

	virtual void onRspSOPQryGroupPosition(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPLockOUnLockStock(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPWithdrawOrder(const dict &data, const dict &error) {};

	virtual void onRspSOPQryEntrustOrder(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQrySerialTrade(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryPosition(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryCollateralPosition(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryCapitalAccountInfo(const dict &data, const dict &error) {};

	virtual void onRspSOPQryAccountInfo(const dict &data, const dict &error) {};

	virtual void onRspSOPQryShareholderInfo(const dict &data, const dict &error) {};

	virtual void onRspSOPCalcAbleEntrustQty(const dict &data, const dict &error) {};

	virtual void onRspSOPQryAbleLockStock(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryContactInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPExectueOrder(const dict &data, const dict &error) {};

	virtual void onRspSOPQryExecAssiInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryTradeTime(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryExchangeInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryCommission(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryDeposit(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPQryContractObjectInfo(const dict &data, const dict &error, bool last) {};

	virtual void onSOPEntrustOrderRtn(const dict &data) {};

	virtual void onSOPTradeRtn(const dict &data) {};

	virtual void onSOPWithdrawOrderRtn(const dict &data) {};

	virtual void onSOPQuoteEntrustOrderRtn(const dict &data) {};

	virtual void onRspSOPCapitalTranInOut(const dict &data, const dict &error) {};

	virtual void onRspSOPCapitalDistributionRatio(const dict &data, const dict &error, bool last) {};

	virtual void onRspSOPFundTransBetweenNodes(const dict &data, const dict &error) {};

	virtual void onRspSOPModCapitalDistributionRatio(const dict &data, const dict &error) {};

	virtual void onRspFASLUserLogin(const dict &data, const dict &error) {};

	virtual void onRspFASLUserLogout(const dict &data, const dict &error) {};

	virtual void onRspFASLQryAbleFinInfo(const dict &data, const dict &error) {};

	virtual void onRspFASLQryAbleSloInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLTransferCollateral(const dict &data, const dict &error) {};

	virtual void onRspFASLDirectRepayment(const dict &data, const dict &error) {};

	virtual void onRspFASLRepayStockTransfer(const dict &data, const dict &error) {};

	virtual void onRspFASLEntrustCrdtOrder(const dict &data, const dict &error) {};

	virtual void onRspFASLEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspFASLCalcAbleEntrustCrdtQty(const dict &data, const dict &error) {};

	virtual void onRspFASLQryCrdtFunds(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryCrdtContract(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryCrdtConChangeInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLTransferFunds(const dict &data, const dict &error) {};

	virtual void onRspFASLTransferStock(const dict &data, const dict &error) {};

	virtual void onRspFASLQryAccountInfo(const dict &data, const dict &error) {};

	virtual void onRspFASLQryCapitalAccountInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryShareholderInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryPosition(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryEntrustOrder(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQrySerialTrade(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryRealTimeTrade(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryFreezeFundsDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryFreezeStockDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryTransferFundsDetail(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLWithdrawOrder(const dict &data, const dict &error) {};

	virtual void onRspFASLQrySystemTime(const dict &data, const dict &error) {};

	virtual void onRspFASLQryTransferredContract(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLDesirableFundsOut(const dict &data, const dict &error) {};

	virtual void onRspFASLQryGuaranteedContract(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryUnderlyingContract(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryCentreFundAvlInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLQryPlacingInterestsInfo(const dict &data, const dict &error, bool last) {};

	virtual void onRspFASLUserPasswordUpdate(const dict &data, const dict &error) {};

	virtual void onFASLEntrustOrderRtn(const dict &data) {};

	virtual void onFASLTradeRtn(const dict &data) {};

	virtual void onFASLWithdrawOrderRtn(const dict &data) {};

	virtual void onFASLLiabilitiesRtn(const dict &data) {};

	virtual void onRspStockETFEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspStockETFBasketOrder(const dict &data, const dict &error, bool last) {};

	virtual void onRspStockBondRepurchaseOrder(const dict &data, const dict &error) {};

	virtual void onRspStockBondInOutStockOrder(const dict &data, const dict &error) {};

	virtual void onRspStockIssueBusinessOrder(const dict &data, const dict &error) {};

	virtual void onRspStockLOFEntrustOrder(const dict &data, const dict &error) {};

	virtual void onRspStockAfterHoursPriceOrder(const dict &data, const dict &error) {};

	virtual void onRspStockNonTradingBusinessOrder(const dict &data, const dict &error) {};

	virtual void onRspStockSHMutualFundOrder(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAblePurchaseETFBasketQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleBondRepurchaseQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleIssueBusinessQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAblePurchaseLOFQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleAfterHoursPriceQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleNonTradingBusinessQty(const dict &data, const dict &error) {};

	virtual void onRspStockCalcAbleSHMutualFundQty(const dict &data, const dict &error) {};

	//-------------------------------------------------------------------------------------
	//req:���������������ֵ�
	//-------------------------------------------------------------------------------------

	void createDFITCSECTraderApi(string pszLogAddr);

	void release();

	int init(string pszFrontAddress);

	int exit();

	int subscribePrivateTopic(int nResumeType);

	int reqStockUserLogin(const dict &req);

	int reqStockUserLogout(const dict &req);

	int reqStockUserPasswordUpdate(const dict &req);

	int reqStockEntrustOrder(const dict &req);

	int reqStockWithdrawOrder(const dict &req);

	int reqStockQryEntrustOrder(const dict &req);

	int reqStockQryRealTimeTrade(const dict &req);

	int reqStockQrySerialTrade(const dict &req);

	int reqStockQryPosition(const dict &req);

	int reqStockQryCapitalAccountInfo(const dict &req);

	int reqStockQryAccountInfo(const dict &req);

	int reqStockQryShareholderInfo(const dict &req);

	int reqStockTransferFunds(const dict &req);

	int reqStockEntrustBatchOrder(const dict &req);

	int reqStockWithdrawBatchOrder(const dict &req);

	int reqStockCalcAbleEntrustQty(const dict &req);

	int reqStockCalcAblePurchaseETFQty(const dict &req);

	int reqStockQryFreezeFundsDetail(const dict &req);

	int reqStockQryFreezeStockDetail(const dict &req);

	int reqStockQryTransferFundsDetail(const dict &req);

	int reqStockQryTransferStockDetail(const dict &req);

	int reqStockQryStockInfo(const dict &req);

	int reqStockQryStockStaticInfo(const dict &req);

	int reqStockQryTradeTime(const dict &req);

	int reqSOPUserLogin(const dict &req);

	int reqSOPUserLogout(const dict &req);

	int reqSOPUserPasswordUpdate(const dict &req);

	int reqSOPEntrustOrder(const dict &req);

	int reqSOPQuoteEntrustOrder(const dict &req);

	int reqSOPGroupSplit(const dict &req);

	int reqSOPGroupExectueOrder(const dict &req);

	int reqSOPQryGroupPosition(const dict &req);

	int reqSOPLockOUnLockStock(const dict &req);

	int reqSOPWithdrawOrder(const dict &req);

	int reqSOPQryEntrustOrder(const dict &req);

	int reqSOPQrySerialTrade(const dict &req);

	int reqSOPQryPosition(const dict &req);

	int reqSOPQryCollateralPosition(const dict &req);

	int reqSOPQryCapitalAccountInfo(const dict &req);

	int reqSOPQryAccountInfo(const dict &req);

	int reqSOPQryShareholderInfo(const dict &req);

	int reqSOPCalcAbleEntrustQty(const dict &req);

	int reqSOPQryAbleLockStock(const dict &req);

	int reqSOPQryContactInfo(const dict &req);

	int reqSOPExectueOrder(const dict &req);

	int reqSOPQryExecAssiInfo(const dict &req);

	int reqSOPQryTradeTime(const dict &req);

	int reqSOPQryExchangeInfo(const dict &req);

	int reqSOPQryCommission(const dict &req);

	int reqSOPQryDeposit(const dict &req);

	int reqSOPQryContractObjectInfo(const dict &req);

	int reqSOPCapitalTranInOut(const dict &req);

	int reqSOPCapitalDistributionRatio(const dict &req);

	int reqSOPFundTransBetweenNodes(const dict &req);

	int reqSOPModCapitalDistributionRatio(const dict &req);

	int reqFASLUserLogin(const dict &req);

	int reqFASLUserLogout(const dict &req);

	int reqFASLQryAbleFinInfo(const dict &req);

	int reqFASLQryAbleSloInfo(const dict &req);

	int reqFASLTransferCollateral(const dict &req);

	int reqFASLDirectRepayment(const dict &req);

	int reqFASLRepayStockTransfer(const dict &req);

	int reqFASLEntrustCrdtOrder(const dict &req);

	int reqFASLEntrustOrder(const dict &req);

	int reqFASLWithdrawOrder(const dict &req);

	int reqFASLCalcAbleEntrustCrdtQty(const dict &req);

	int reqFASLQryCrdtFunds(const dict &req);

	int reqFASLQryCrdtContract(const dict &req);

	int reqFASLQryCrdtConChangeInfo(const dict &req);

	int reqFASLTransferFunds(const dict &req);

	int reqFASLTransferStock(const dict &req);

	int reqFASLQryAccountInfo(const dict &req);

	int reqFASLQryCapitalAccountInfo(const dict &req);

	int reqFASLQryShareholderInfo(const dict &req);

	int reqFASLQryPosition(const dict &req);

	int reqFASLQryEntrustOrder(const dict &req);

	int reqFASLQrySerialTrade(const dict &req);

	int reqFASLQryRealTimeTrade(const dict &req);

	int reqFASLQryFreezeFundsDetail(const dict &req);

	int reqFASLQryFreezeStockDetail(const dict &req);

	int reqFASLQryTransferFundsDetail(const dict &req);

	int reqFASLQrySystemTime(const dict &req);

	int reqFASLQryTransferredContract(const dict &req);

	int reqFASLDesirableFundsOut(const dict &req);

	int reqFASLQryGuaranteedContract(const dict &req);

	int reqFASLQryUnderlyingContract(const dict &req);

	int reqFASLQryCentreFundAvlInfo(const dict &req);

	int reqFASLQryPlacingInterestsInfo(const dict &req);

	int reqFASLUserPasswordUpdate(const dict &req);

	int reqStockETFEntrustOrder(const dict &req);

	int reqStockETFBasketOrder(const dict &req);

	int reqStockBondRepurchaseOrder(const dict &req);

	int reqStockBondInOutStockOrder(const dict &req);

	int reqStockIssueBusinessOrder(const dict &req);

	int reqStockLOFEntrustOrder(const dict &req);

	int reqStockAfterHoursPriceOrder(const dict &req);

	int reqStockNonTradingBusinessOrder(const dict &req);

	int reqStockSHMutualFundOrder(const dict &req);

	int reqStockCalcAblePurchaseETFBasketQty(const dict &req);

	int reqStockCalcAbleBondRepurchaseQty(const dict &req);

	int reqStockCalcAbleIssueBusinessQty(const dict &req);

	int reqStockCalcAblePurchaseLOFQty(const dict &req);

	int reqStockCalcAbleAfterHoursPriceQty(const dict &req);

	int reqStockCalcAbleNonTradingBusinessQty(const dict &req);

	int reqStockCalcAbleSHMutualFundQty(const dict &req);

};
