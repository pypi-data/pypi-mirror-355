//ϵͳ
#ifdef WIN32
#include "pch.h"
#endif

#include "vntora.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "TORATstpTraderApi.h"


using namespace pybind11;
using namespace TORASTOCKAPI;
using namespace std;


#define ONFRONTCONNECTED 0
#define ONFRONTDISCONNECTED 1
#define ONRSPERROR 2
#define ONRSPGETCONNECTIONINFO 3
#define ONRSPUSERLOGIN 4
#define ONRSPUSERLOGOUT 5
#define ONRSPUSERPASSWORDUPDATE 6
#define ONRSPINPUTDEVICESERIAL 7
#define ONRSPORDERINSERT 8
#define ONRTNORDER 9
#define ONERRRTNORDERINSERT 10
#define ONRTNTRADE 11
#define ONRSPORDERACTION 12
#define ONERRRTNORDERACTION 13
#define ONRSPCONDORDERINSERT 14
#define ONRTNCONDORDER 15
#define ONERRRTNCONDORDERINSERT 16
#define ONRSPCONDORDERACTION 17
#define ONERRRTNCONDORDERACTION 18
#define ONRSPNEGOORDERINSERT 19
#define ONRTNNEGOORDER 20
#define ONERRRTNNEGOORDERINSERT 21
#define ONRTNNEGOTRADE 22
#define ONRSPNEGOORDERACTION 23
#define ONERRRTNNEGOORDERACTION 24
#define ONRSPORDERINSERTEX 25
#define ONRSPORDERACTIONEX 26
#define ONRTNMARKETSTATUS 27
#define ONRSPTRANSFERFUND 28
#define ONERRRTNTRANSFERFUND 29
#define ONRTNTRANSFERFUND 30
#define ONRSPTRANSFERPOSITION 31
#define ONERRRTNTRANSFERPOSITION 32
#define ONRTNTRANSFERPOSITION 33
#define ONRTNPERIPHERYTRANSFERPOSITION 34
#define ONRTNPERIPHERYTRANSFERFUND 35
#define ONRSPINQUIRYJZFUND 36
#define ONRSPINQUIRYBANKACCOUNTFUND 37
#define ONRTNTRADINGNOTICE 38
#define ONRSPINQUIRYMAXORDERVOLUME 39
#define ONRSPINQUIRYTRADECONCENTRATION 40
#define ONRSPMODIFYOPENPOSCOST 41
#define ONRSPINPUTNODEFUNDASSIGNMENT 42
#define ONRSPINQUIRYNODEFUNDASSIGNMENT 43
#define ONRSPQRYEXCHANGE 44
#define ONRSPQRYSECURITY 45
#define ONRSPQRYIPOINFO 46
#define ONRSPQRYUSER 47
#define ONRSPQRYINVESTOR 48
#define ONRSPQRYSHAREHOLDERACCOUNT 49
#define ONRSPQRYRATIONALINFO 50
#define ONRSPQRYORDER 51
#define ONRSPQRYORDERACTION 52
#define ONRSPQRYTRADE 53
#define ONRSPQRYTRADINGACCOUNT 54
#define ONRSPQRYPOSITION 55
#define ONRSPQRYTRADINGFEE 56
#define ONRSPQRYINVESTORTRADINGFEE 57
#define ONRSPQRYIPOQUOTA 58
#define ONRSPQRYORDERFUNDDETAIL 59
#define ONRSPQRYFUNDTRANSFERDETAIL 60
#define ONRSPQRYPOSITIONTRANSFERDETAIL 61
#define ONRSPQRYPERIPHERYPOSITIONTRANSFERDETAIL 62
#define ONRSPQRYPERIPHERYFUNDTRANSFERDETAIL 63
#define ONRSPQRYBONDCONVERSIONINFO 64
#define ONRSPQRYBONDPUTBACKINFO 65
#define ONRSPQRYINVESTORCONDORDERLIMITPARAM 66
#define ONRSPQRYCONDITIONORDER 67
#define ONRSPQRYCONDORDERACTION 68
#define ONRSPQRYTRADINGNOTICE 69
#define ONRSPQRYIPONUMBERRESULT 70
#define ONRSPQRYIPOMATCHNUMBERRESULT 71
#define ONRSPQRYSHAREHOLDERSPECPRIVILEGE 72
#define ONRSPQRYMARKET 73
#define ONRSPQRYETFFILE 74
#define ONRSPQRYETFBASKET 75
#define ONRSPQRYINVESTORPOSITIONLIMIT 76
#define ONRSPQRYSZSEIMCPARAMS 77
#define ONRSPQRYSZSEIMCEXCHANGERATE 78
#define ONRSPQRYSZSEHKPRICETICKINFO 79
#define ONRSPQRYLOFFUNDINFO 80
#define ONRSPQRYPLEDGEPOSITION 81
#define ONRSPQRYPLEDGEINFO 82
#define ONRSPQRYSYSTEMNODEINFO 83
#define ONRSPQRYSTANDARDBONDPOSITION 84
#define ONRSPQRYPREMATURITYREPOORDER 85
#define ONRSPQRYNEGOORDER 86
#define ONRSPQRYNEGOORDERACTION 87
#define ONRSPQRYNEGOTRADE 88
#define ONRSPQRYNEGOTIATIONPARAM 89


///-------------------------------------------------------------------------------------
///C++ SPI�Ļص���������ʵ��
///-------------------------------------------------------------------------------------

//API�ļ̳�ʵ��
class StockApi : public CTORATstpTraderSpi
{
private:
	TRADER_API_DLL_EXPORT CTORATstpTraderApi* api;      //API����
	bool active = false;                //����״̬
	thread task_thread;                    //�����߳�ָ�루��python���������ݣ�
	TaskQueue task_queue;                //�������
	bool logging = false;


public:
	StockApi()
	{
	};

	~StockApi()
	{
		if (this->active)
		{
			this->exit();
		}
	};


	//-------------------------------------------------------------------------------------
	//API�ص�����
	//-------------------------------------------------------------------------------------

	///���ͻ����뽻�׺�̨������ͨ������ʱ����δ��¼ǰ�����÷��������á�
	virtual void OnFrontConnected();

	///���ͻ����뽻�׺�̨ͨ�����ӶϿ�ʱ���÷��������á���������������API���Զ��������ӣ��ͻ��˿ɲ�������
	///@param nReason ����ԭ��
	///        -3 �����ѶϿ�
	///        -4 �����ʧ��
	///        -5 ����дʧ��
	///        -6 ����������
	///        -7 ����Ŵ���
	///        -8 �������������
	///        -9 ����ı���
	///		  -15 �����ʧ��
	///		  -16 ����дʧ��
	virtual void OnFrontDisconnected(int nReason);

	///����Ӧ��
	virtual void OnRspError(CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ȡ������ϢӦ��
	virtual void OnRspGetConnectionInfo(CTORATstpConnectionInfoField* pConnectionInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��¼��Ӧ
	virtual void OnRspUserLogin(CTORATstpRspUserLoginField* pRspUserLoginField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�ǳ���Ӧ
	virtual void OnRspUserLogout(CTORATstpUserLogoutField* pUserLogoutField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�޸�������Ӧ
	virtual void OnRspUserPasswordUpdate(CTORATstpUserPasswordUpdateField* pUserPasswordUpdateField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///¼���豸������Ӧ
	virtual void OnRspInputDeviceSerial(CTORATstpRspInputDeviceSerialField* pRspInputDeviceSerialField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///����¼����Ӧ
	virtual void OnRspOrderInsert(CTORATstpInputOrderField* pInputOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�����ر�
	virtual void OnRtnOrder(CTORATstpOrderField* pOrderField);

	///��������ر�
	virtual void OnErrRtnOrderInsert(CTORATstpInputOrderField* pInputOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�ɽ��ر�
	virtual void OnRtnTrade(CTORATstpTradeField* pTradeField);

	///������Ӧ
	virtual void OnRspOrderAction(CTORATstpInputOrderActionField* pInputOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��������ر�
	virtual void OnErrRtnOrderAction(CTORATstpInputOrderActionField* pInputOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///������¼����Ӧ
	virtual void OnRspCondOrderInsert(CTORATstpInputCondOrderField* pInputCondOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�������ر�
	virtual void OnRtnCondOrder(CTORATstpConditionOrderField* pConditionOrderField);

	///������¼�����ر�
	virtual void OnErrRtnCondOrderInsert(CTORATstpInputCondOrderField* pInputCondOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///������������Ӧ
	virtual void OnRspCondOrderAction(CTORATstpInputCondOrderActionField* pInputCondOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��������������ر�
	virtual void OnErrRtnCondOrderAction(CTORATstpInputCondOrderActionField* pInputCondOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///Э�齻�ױ���¼����Ӧ
	virtual void OnRspNegoOrderInsert(CTORATstpInputNegoOrderField* pInputNegoOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///Э�齻�ױ����ر�
	virtual void OnRtnNegoOrder(CTORATstpNegoOrderField* pNegoOrderField);

	///Э�齻�ױ�������ر�
	virtual void OnErrRtnNegoOrderInsert(CTORATstpInputNegoOrderField* pInputNegoOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///Э�齻�׳ɽ��ر�
	virtual void OnRtnNegoTrade(CTORATstpNegoTradeField* pNegoTradeField);

	///Э�齻�ױ�������¼����Ӧ
	virtual void OnRspNegoOrderAction(CTORATstpInputNegoOrderActionField* pInputNegoOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///Э�齻�ױ�����������ر�
	virtual void OnErrRtnNegoOrderAction(CTORATstpInputNegoOrderActionField* pInputNegoOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///����¼����Ӧ����չ��
	virtual void OnRspOrderInsertEx(CTORATstpInputOrderExField* pInputOrderExField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///����������Ӧ����չ��
	virtual void OnRspOrderActionEx(CTORATstpInputOrderActionExField* pInputOrderActionExField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�г�״̬�ر�
	virtual void OnRtnMarketStatus(CTORATstpMarketStatusField* pMarketStatusField);

	///�ʽ�ת����Ӧ
	virtual void OnRspTransferFund(CTORATstpInputTransferFundField* pInputTransferFundField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�ʽ�ת�ƴ���ر�
	virtual void OnErrRtnTransferFund(CTORATstpInputTransferFundField* pInputTransferFundField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�ʽ�ת�ƻر�
	virtual void OnRtnTransferFund(CTORATstpTransferFundField* pTransferFundField);

	///��λת����Ӧ
	virtual void OnRspTransferPosition(CTORATstpInputTransferPositionField* pInputTransferPositionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��λת�ƴ���ر�
	virtual void OnErrRtnTransferPosition(CTORATstpInputTransferPositionField* pInputTransferPositionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��λת�ƻر�
	virtual void OnRtnTransferPosition(CTORATstpTransferPositionField* pTransferPositionField);

	///��Χϵͳ��λת�ƻر�
	virtual void OnRtnPeripheryTransferPosition(CTORATstpPeripheryTransferPositionField* pPeripheryTransferPositionField);

	///��Χϵͳ�ʽ�ת�ƻر�
	virtual void OnRtnPeripheryTransferFund(CTORATstpPeripheryTransferFundField* pPeripheryTransferFundField);

	///��ѯ���н���ϵͳ�ʽ���Ӧ
	virtual void OnRspInquiryJZFund(CTORATstpRspInquiryJZFundField* pRspInquiryJZFundField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��ѯ�����˻������Ӧ
	virtual void OnRspInquiryBankAccountFund(CTORATstpRspInquiryBankAccountFundField* pRspInquiryBankAccountFundField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///����֪ͨ�ر�
	virtual void OnRtnTradingNotice(CTORATstpTradingNoticeField* pTradingNoticeField);

	///��ѯ��󱨵�����Ӧ
	virtual void OnRspInquiryMaxOrderVolume(CTORATstpRspInquiryMaxOrderVolumeField* pRspInquiryMaxOrderVolumeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///���׳ɽ����жȲ�ѯ��Ӧ
	virtual void OnRspInquiryTradeConcentration(CTORATstpInquiryTradeConcentrationField* pInquiryTradeConcentrationField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///�����޸Ŀ��ֳɱ���Ӧ
	virtual void OnRspModifyOpenPosCost(CTORATstpReqModifyOpenPosCostField* pReqModifyOpenPosCostField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///¼��ڵ��ʽ������Ϣ��Ӧ
	virtual void OnRspInputNodeFundAssignment(CTORATstpInputNodeFundAssignmentField* pInputNodeFundAssignmentField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��ѯ�ڵ��ʽ���������Ӧ
	virtual void OnRspInquiryNodeFundAssignment(CTORATstpRspInquiryNodeFundAssignmentField* pRspInquiryNodeFundAssignmentField, CTORATstpRspInfoField* pRspInfoField, int nRequestID);

	///��ѯ��������Ӧ
	virtual void OnRspQryExchange(CTORATstpExchangeField* pExchangeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ֤ȯ��Ϣ��Ӧ
	virtual void OnRspQrySecurity(CTORATstpSecurityField* pSecurityField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�¹���Ϣ��Ӧ
	virtual void OnRspQryIPOInfo(CTORATstpIPOInfoField* pIPOInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�û���Ӧ
	virtual void OnRspQryUser(CTORATstpUserField* pUserField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯͶ������Ӧ
	virtual void OnRspQryInvestor(CTORATstpInvestorField* pInvestorField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ɶ��˻���Ӧ
	virtual void OnRspQryShareholderAccount(CTORATstpShareholderAccountField* pShareholderAccountField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�����ծ��Ϣ��Ӧ
	virtual void OnRspQryRationalInfo(CTORATstpRationalInfoField* pRationalInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ������Ӧ
	virtual void OnRspQryOrder(CTORATstpOrderField* pOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ��������
	virtual void OnRspQryOrderAction(CTORATstpOrderActionField* pOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ɽ���Ӧ
	virtual void OnRspQryTrade(CTORATstpTradeField* pTradeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ʽ��˻���Ӧ
	virtual void OnRspQryTradingAccount(CTORATstpTradingAccountField* pTradingAccountField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯͶ���ֲ߳���Ӧ
	virtual void OnRspQryPosition(CTORATstpPositionField* pPositionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�������׷�����Ӧ
	virtual void OnRspQryTradingFee(CTORATstpTradingFeeField* pTradingFeeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯӶ�������Ӧ
	virtual void OnRspQryInvestorTradingFee(CTORATstpInvestorTradingFeeField* pInvestorTradingFeeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�¹��깺�����Ӧ
	virtual void OnRspQryIPOQuota(CTORATstpIPOQuotaField* pIPOQuotaField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ������ϸ�ʽ���Ӧ
	virtual void OnRspQryOrderFundDetail(CTORATstpOrderFundDetailField* pOrderFundDetailField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ʽ�ת����ˮ��Ӧ
	virtual void OnRspQryFundTransferDetail(CTORATstpFundTransferDetailField* pFundTransferDetailField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�ֲ�ת����ˮ��Ӧ
	virtual void OnRspQryPositionTransferDetail(CTORATstpPositionTransferDetailField* pPositionTransferDetailField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ��Χϵͳ��λ������ˮ��Ӧ
	virtual void OnRspQryPeripheryPositionTransferDetail(CTORATstpPeripheryPositionTransferDetailField* pPeripheryPositionTransferDetailField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ��Χϵͳ�ʽ������ˮ��Ӧ
	virtual void OnRspQryPeripheryFundTransferDetail(CTORATstpPeripheryFundTransferDetailField* pPeripheryFundTransferDetailField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯծȯת����Ϣ��Ӧ
	virtual void OnRspQryBondConversionInfo(CTORATstpBondConversionInfoField* pBondConversionInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯծȯ������Ϣ��Ӧ
	virtual void OnRspQryBondPutbackInfo(CTORATstpBondPutbackInfoField* pBondPutbackInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯͶ�������������Ʋ�����Ӧ
	virtual void OnRspQryInvestorCondOrderLimitParam(CTORATstpInvestorCondOrderLimitParamField* pInvestorCondOrderLimitParamField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ��������Ӧ
	virtual void OnRspQryConditionOrder(CTORATstpConditionOrderField* pConditionOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ������������Ӧ
	virtual void OnRspQryCondOrderAction(CTORATstpCondOrderActionField* pCondOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ����֪ͨ��Ӧ
	virtual void OnRspQryTradingNotice(CTORATstpTradingNoticeField* pTradingNoticeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�¹��깺��Ž����Ӧ
	virtual void OnRspQryIPONumberResult(CTORATstpIPONumberResultField* pIPONumberResultField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�¹��깺��ǩ�����Ӧ
	virtual void OnRspQryIPOMatchNumberResult(CTORATstpIPOMatchNumberResultField* pIPOMatchNumberResultField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ����Э����Ӧ
	virtual void OnRspQryShareholderSpecPrivilege(CTORATstpShareholderSpecPrivilegeField* pShareholderSpecPrivilegeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ�г���Ӧ
	virtual void OnRspQryMarket(CTORATstpMarketField* pMarketField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯETF�嵥��Ϣ��Ӧ
	virtual void OnRspQryETFFile(CTORATstpETFFileField* pETFFileField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯETF�ɷ�֤ȯ��Ϣ��Ӧ
	virtual void OnRspQryETFBasket(CTORATstpETFBasketField* pETFBasketField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯͶ�����޲���Ϣ��Ӧ
	virtual void OnRspQryInvestorPositionLimit(CTORATstpInvestorPositionLimitField* pInvestorPositionLimitField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ���ͨ�����г�����״̬��Ϣ��Ӧ
	virtual void OnRspQrySZSEImcParams(CTORATstpSZSEImcParamsField* pSZSEImcParamsField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ���ͨ�����г�����������Ϣ��Ӧ
	virtual void OnRspQrySZSEImcExchangeRate(CTORATstpSZSEImcExchangeRateField* pSZSEImcExchangeRateField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ���ͨ��С�۲���Ϣ��Ӧ
	virtual void OnRspQrySZSEHKPriceTickInfo(CTORATstpSZSEHKPriceTickInfoField* pSZSEHKPriceTickInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯLOF������Ϣ��Ӧ
	virtual void OnRspQryLofFundInfo(CTORATstpLofFundInfoField* pLofFundInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯͶ������Ѻ�ֲ���Ӧ
	virtual void OnRspQryPledgePosition(CTORATstpPledgePositionField* pPledgePositionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ֤ȯ��Ѻ��Ϣ��Ӧ
	virtual void OnRspQryPledgeInfo(CTORATstpPledgeInfoField* pPledgeInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯϵͳ�ڵ���Ϣ��Ӧ
	virtual void OnRspQrySystemNodeInfo(CTORATstpSystemNodeInfoField* pSystemNodeInfoField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯ��׼ȯ�����Ӧ
	virtual void OnRspQryStandardBondPosition(CTORATstpStandardBondPositionField* pStandardBondPositionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯδ����ծȯ��Ѻ�ع�ί����Ӧ
	virtual void OnRspQryPrematurityRepoOrder(CTORATstpPrematurityRepoOrderField* pPrematurityRepoOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯЭ�齻�ױ�����Ӧ
	virtual void OnRspQryNegoOrder(CTORATstpNegoOrderField* pNegoOrderField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯЭ�齻�׳�����Ӧ
	virtual void OnRspQryNegoOrderAction(CTORATstpNegoOrderActionField* pNegoOrderActionField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯЭ�齻�׳ɽ���Ӧ
	virtual void OnRspQryNegoTrade(CTORATstpNegoTradeField* pNegoTradeField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);

	///��ѯЭ�齻�ײ�����Ӧ
	virtual void OnRspQryNegotiationParam(CTORATstpNegotiationParamField* pNegotiationParamField, CTORATstpRspInfoField* pRspInfoField, int nRequestID, bool bIsLast);


	//-------------------------------------------------------------------------------------
	//data���ص������������ֵ�
	//-------------------------------------------------------------------------------------
	
	virtual void onFrontConnected() {};

	virtual void onFrontDisconnected(int nReason) {};

	virtual void onRspError(const dict& error, int nRequestID, bool last) {};

	virtual void onRspGetConnectionInfo(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspUserLogin(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspUserLogout(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspUserPasswordUpdate(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInputDeviceSerial(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnOrder(const dict& data) {};

	virtual void onErrRtnOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTrade(const dict& data) {};

	virtual void onRspOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCondOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnCondOrder(const dict& data) {};

	virtual void onErrRtnCondOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCondOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnCondOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspNegoOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnNegoOrder(const dict& data) {};

	virtual void onErrRtnNegoOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnNegoTrade(const dict& data) {};

	virtual void onRspNegoOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnNegoOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspOrderInsertEx(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspOrderActionEx(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnMarketStatus(const dict& data) {};

	virtual void onRspTransferFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnTransferFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTransferFund(const dict& data) {};

	virtual void onRspTransferPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnTransferPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTransferPosition(const dict& data) {};

	virtual void onRtnPeripheryTransferPosition(const dict& data) {};

	virtual void onRtnPeripheryTransferFund(const dict& data) {};

	virtual void onRspInquiryJZFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryBankAccountFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTradingNotice(const dict& data) {};

	virtual void onRspInquiryMaxOrderVolume(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryTradeConcentration(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspModifyOpenPosCost(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInputNodeFundAssignment(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryNodeFundAssignment(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspQryExchange(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySecurity(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryIPOInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryUser(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestor(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryShareholderAccount(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryRationalInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTrade(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingAccount(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingFee(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorTradingFee(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryIPOQuota(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrderFundDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryFundTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPositionTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPeripheryPositionTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPeripheryFundTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryBondConversionInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryBondPutbackInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorCondOrderLimitParam(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryConditionOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCondOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingNotice(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryIPONumberResult(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryIPOMatchNumberResult(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryShareholderSpecPrivilege(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryMarket(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryETFFile(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryETFBasket(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorPositionLimit(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySZSEImcParams(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySZSEImcExchangeRate(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySZSEHKPriceTickInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryLofFundInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPledgePosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPledgeInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySystemNodeInfo(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryStandardBondPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPrematurityRepoOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryNegoOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryNegoOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryNegoTrade(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryNegotiationParam(const dict& data, const dict& error, int nRequestID, bool last) {};

	//-------------------------------------------------------------------------------------
	//task������
	//-------------------------------------------------------------------------------------

	void processTask();

	void processFrontConnected(Task* task);

	void processFrontDisconnected(Task* task);

	void processRspError(Task* task);

	void processRspGetConnectionInfo(Task* task);

	void processRspUserLogin(Task* task);

	void processRspUserLogout(Task* task);

	void processRspUserPasswordUpdate(Task* task);

	void processRspInputDeviceSerial(Task* task);

	void processRspOrderInsert(Task* task);

	void processRtnOrder(Task* task);

	void processErrRtnOrderInsert(Task* task);

	void processRtnTrade(Task* task);

	void processRspOrderAction(Task* task);

	void processErrRtnOrderAction(Task* task);

	void processRspCondOrderInsert(Task* task);

	void processRtnCondOrder(Task* task);

	void processErrRtnCondOrderInsert(Task* task);

	void processRspCondOrderAction(Task* task);

	void processErrRtnCondOrderAction(Task* task);

	void processRspNegoOrderInsert(Task* task);

	void processRtnNegoOrder(Task* task);

	void processErrRtnNegoOrderInsert(Task* task);

	void processRtnNegoTrade(Task* task);

	void processRspNegoOrderAction(Task* task);

	void processErrRtnNegoOrderAction(Task* task);

	void processRspOrderInsertEx(Task* task);

	void processRspOrderActionEx(Task* task);

	void processRtnMarketStatus(Task* task);

	void processRspTransferFund(Task* task);

	void processErrRtnTransferFund(Task* task);

	void processRtnTransferFund(Task* task);

	void processRspTransferPosition(Task* task);

	void processErrRtnTransferPosition(Task* task);

	void processRtnTransferPosition(Task* task);

	void processRtnPeripheryTransferPosition(Task* task);

	void processRtnPeripheryTransferFund(Task* task);

	void processRspInquiryJZFund(Task* task);

	void processRspInquiryBankAccountFund(Task* task);

	void processRtnTradingNotice(Task* task);

	void processRspInquiryMaxOrderVolume(Task* task);

	void processRspInquiryTradeConcentration(Task* task);

	void processRspModifyOpenPosCost(Task* task);

	void processRspInputNodeFundAssignment(Task* task);

	void processRspInquiryNodeFundAssignment(Task* task);

	void processRspQryExchange(Task* task);

	void processRspQrySecurity(Task* task);

	void processRspQryIPOInfo(Task* task);

	void processRspQryUser(Task* task);

	void processRspQryInvestor(Task* task);

	void processRspQryShareholderAccount(Task* task);

	void processRspQryRationalInfo(Task* task);

	void processRspQryOrder(Task* task);

	void processRspQryOrderAction(Task* task);

	void processRspQryTrade(Task* task);

	void processRspQryTradingAccount(Task* task);

	void processRspQryPosition(Task* task);

	void processRspQryTradingFee(Task* task);

	void processRspQryInvestorTradingFee(Task* task);

	void processRspQryIPOQuota(Task* task);

	void processRspQryOrderFundDetail(Task* task);

	void processRspQryFundTransferDetail(Task* task);

	void processRspQryPositionTransferDetail(Task* task);

	void processRspQryPeripheryPositionTransferDetail(Task* task);

	void processRspQryPeripheryFundTransferDetail(Task* task);

	void processRspQryBondConversionInfo(Task* task);

	void processRspQryBondPutbackInfo(Task* task);

	void processRspQryInvestorCondOrderLimitParam(Task* task);

	void processRspQryConditionOrder(Task* task);

	void processRspQryCondOrderAction(Task* task);

	void processRspQryTradingNotice(Task* task);

	void processRspQryIPONumberResult(Task* task);

	void processRspQryIPOMatchNumberResult(Task* task);

	void processRspQryShareholderSpecPrivilege(Task* task);

	void processRspQryMarket(Task* task);

	void processRspQryETFFile(Task* task);

	void processRspQryETFBasket(Task* task);

	void processRspQryInvestorPositionLimit(Task* task);

	void processRspQrySZSEImcParams(Task* task);

	void processRspQrySZSEImcExchangeRate(Task* task);

	void processRspQrySZSEHKPriceTickInfo(Task* task);

	void processRspQryLofFundInfo(Task* task);

	void processRspQryPledgePosition(Task* task);

	void processRspQryPledgeInfo(Task* task);

	void processRspQrySystemNodeInfo(Task* task);

	void processRspQryStandardBondPosition(Task* task);

	void processRspQryPrematurityRepoOrder(Task* task);

	void processRspQryNegoOrder(Task* task);

	void processRspQryNegoOrderAction(Task* task);

	void processRspQryNegoTrade(Task* task);

	void processRspQryNegotiationParam(Task* task);

	//-------------------------------------------------------------------------------------
	//req:���������������ֵ�
	//-------------------------------------------------------------------------------------

	void createTstpTraderApi(string pszFlowPath, bool bEncrypt);

	void registerFront(string pszFrontAddress);

	void init();

	int join();

	void release();

	string getApiVersion();

	int exit();

	void registerNameServer(string pszNsAddress);

	void registerFensUserInfo(const dict& req);

	void subscribePrivateTopic(int type);

	void subscribePublicTopic(int type);

	int reqGetConnectionInfo(int nrequestid);

	int reqUserLogin(const dict& req, int nrequestid);

	int reqUserLogout(const dict& req, int nrequestid);

	int reqUserPasswordUpdate(const dict& req, int nrequestid);

	int reqInputDeviceSerial(const dict& req, int nrequestid);

	int reqOrderInsert(const dict& req, int nrequestid);

	int reqOrderAction(const dict& req, int nrequestid);

	int reqCondOrderInsert(const dict& req, int nrequestid);

	int reqCondOrderAction(const dict& req, int nrequestid);

	int reqNegoOrderInsert(const dict& req, int nrequestid);

	int reqNegoOrderAction(const dict& req, int nrequestid);

	int reqOrderInsertEx(const dict& req, int nrequestid);

	int reqOrderActionEx(const dict& req, int nrequestid);

	int reqTransferFund(const dict& req, int nrequestid);

	int reqTransferPosition(const dict& req, int nrequestid);

	int reqInquiryJZFund(const dict& req, int nrequestid);

	int reqInquiryBankAccountFund(const dict& req, int nrequestid);

	int reqInquiryMaxOrderVolume(const dict& req, int nrequestid);

	int reqInquiryTradeConcentration(const dict& req, int nrequestid);

	int reqModifyOpenPosCost(const dict& req, int nrequestid);

	int reqInputNodeFundAssignment(const dict& req, int nrequestid);

	int reqInquiryNodeFundAssignment(const dict& req, int nrequestid);

	int reqQryExchange(const dict& req, int nrequestid);

	int reqQrySecurity(const dict& req, int nrequestid);

	int reqQryIPOInfo(const dict& req, int nrequestid);

	int reqQryUser(const dict& req, int nrequestid);

	int reqQryInvestor(const dict& req, int nrequestid);

	int reqQryShareholderAccount(const dict& req, int nrequestid);

	int reqQryRationalInfo(const dict& req, int nrequestid);

	int reqQryOrder(const dict& req, int nrequestid);

	int reqQryOrderAction(const dict& req, int nrequestid);

	int reqQryTrade(const dict& req, int nrequestid);

	int reqQryTradingAccount(const dict& req, int nrequestid);

	int reqQryPosition(const dict& req, int nrequestid);

	int reqQryTradingFee(const dict& req, int nrequestid);

	int reqQryInvestorTradingFee(const dict& req, int nrequestid);

	int reqQryIPOQuota(const dict& req, int nrequestid);

	int reqQryOrderFundDetail(const dict& req, int nrequestid);

	int reqQryFundTransferDetail(const dict& req, int nrequestid);

	int reqQryPositionTransferDetail(const dict& req, int nrequestid);

	int reqQryPeripheryPositionTransferDetail(const dict& req, int nrequestid);

	int reqQryPeripheryFundTransferDetail(const dict& req, int nrequestid);

	int reqQryBondConversionInfo(const dict& req, int nrequestid);

	int reqQryBondPutbackInfo(const dict& req, int nrequestid);

	int reqQryInvestorCondOrderLimitParam(const dict& req, int nrequestid);

	int reqQryConditionOrder(const dict& req, int nrequestid);

	int reqQryCondOrderAction(const dict& req, int nrequestid);

	int reqQryTradingNotice(const dict& req, int nrequestid);

	int reqQryIPONumberResult(const dict& req, int nrequestid);

	int reqQryIPOMatchNumberResult(const dict& req, int nrequestid);

	int reqQryShareholderSpecPrivilege(const dict& req, int nrequestid);

	int reqQryMarket(const dict& req, int nrequestid);

	int reqQryETFFile(const dict& req, int nrequestid);

	int reqQryETFBasket(const dict& req, int nrequestid);

	int reqQryInvestorPositionLimit(const dict& req, int nrequestid);

	int reqQrySZSEImcParams(const dict& req, int nrequestid);

	int reqQrySZSEImcExchangeRate(const dict& req, int nrequestid);

	int reqQrySZSEHKPriceTickInfo(const dict& req, int nrequestid);

	int reqQryLofFundInfo(const dict& req, int nrequestid);

	int reqQryPledgePosition(const dict& req, int nrequestid);

	int reqQryPledgeInfo(const dict& req, int nrequestid);

	int reqQrySystemNodeInfo(const dict& req, int nrequestid);

	int reqQryStandardBondPosition(const dict& req, int nrequestid);

	int reqQryPrematurityRepoOrder(const dict& req, int nrequestid);

	int reqQryNegoOrder(const dict& req, int nrequestid);

	int reqQryNegoOrderAction(const dict& req, int nrequestid);

	int reqQryNegoTrade(const dict& req, int nrequestid);

	int reqQryNegotiationParam(const dict& req, int nrequestid);
};
