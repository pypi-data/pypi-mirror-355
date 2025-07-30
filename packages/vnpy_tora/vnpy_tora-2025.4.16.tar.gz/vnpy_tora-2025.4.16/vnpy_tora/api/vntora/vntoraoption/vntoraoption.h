//ϵͳ
#ifdef WIN32
#include "pch.h"
#endif

#include "vntora.h"
#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "TORATstpSPTraderApi.h"


using namespace pybind11;
using namespace TORASPAPI;
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
#define ONRSPORDERACTION 11
#define ONERRRTNORDERACTION 12
#define ONRTNTRADE 13
#define ONRSPEXERCISEINSERT 14
#define ONRTNEXERCISE 15
#define ONERRRTNEXERCISEINSERT 16
#define ONRSPEXERCISEACTION 17
#define ONERRRTNEXERCISEACTION 18
#define ONRSPLOCKINSERT 19
#define ONRTNLOCK 20
#define ONERRRTNLOCKINSERT 21
#define ONRSPLOCKACTION 22
#define ONERRRTNLOCKACTION 23
#define ONRTNSTOCKDISPOSAL 24
#define ONRSPCOMBORDERINSERT 25
#define ONRTNCOMBORDER 26
#define ONERRRTNCOMBORDERINSERT 27
#define ONRSPCOMBORDERACTION 28
#define ONERRRTNCOMBORDERACTION 29
#define ONRSPCONDORDERINSERT 30
#define ONRTNCONDORDER 31
#define ONERRRTNCONDORDERINSERT 32
#define ONRSPCONDORDERACTION 33
#define ONERRRTNCONDORDERACTION 34
#define ONRSPCOMBEXERCISEINSERT 35
#define ONRTNCOMBEXERCISE 36
#define ONERRRTNCOMBEXERCISEINSERT 37
#define ONRSPCOMBEXERCISEACTION 38
#define ONERRRTNCOMBEXERCISEACTION 39
#define ONRSPINQUIRYMAXLOCKVOLUME 40
#define ONRSPINQUIRYMAXCOVERVOLUME 41
#define ONRSPINQUIRYSPLITCOMBMARGINDIFFERENCE 42
#define ONRSPTRANSFERFUND 43
#define ONRTNTRANSFERFUND 44
#define ONERRRTNTRANSFERFUND 45
#define ONRTNTRANSFERPOSITION 46
#define ONERRRTNTRANSFERPOSITION 47
#define ONRSPTRANSFERSTOCKPOSITION 48
#define ONRTNTRANSFERSTOCKPOSITION 49
#define ONERRRTNTRANSFERSTOCKPOSITION 50
#define ONRSPINQUIRYJZFUND 51
#define ONRSPINQUIRYBANKACCOUNTFUND 52
#define ONRSPINQUIRYSTOCKPOSITION 53
#define ONRTNMARKETSTATUS 54
#define ONRTNTRADINGNOTICE 55
#define ONRSPQRYEXCHANGE 56
#define ONRSPQRYMARKETDATA 57
#define ONRSPQRYSECURITY 58
#define ONRSPQRYBUPROXY 59
#define ONRSPQRYUSER 60
#define ONRSPQRYINVESTOR 61
#define ONRSPQRYSHAREHOLDERACCOUNT 62
#define ONRSPQRYTRADINGACCOUNT 63
#define ONRSPQRYORDER 64
#define ONRSPQRYTRADE 65
#define ONRSPQRYPOSITION 66
#define ONRSPQRYTRADINGFEE 67
#define ONRSPQRYINVESTORTRADINGFEE 68
#define ONRSPQRYINVESTORMARGINFEE 69
#define ONRSPQRYORDERFUNDDETAIL 70
#define ONRSPQRYFUNDTRANSFERDETAIL 71
#define ONRSPQRYPOSITIONTRANSFERDETAIL 72
#define ONRSPQRYORDERACTION 73
#define ONRSPQRYSTOCKPOSITION 74
#define ONRSPQRYLOCK 75
#define ONRSPQRYEXERCISE 76
#define ONRSPQRYLOCKPOSITION 77
#define ONRSPQRYEXERCISEACTION 78
#define ONRSPQRYLOCKACTION 79
#define ONRSPQRYSTOCKPOSITIONTRANSFERDETAIL 80
#define ONRSPQRYTRADINGNOTICE 81
#define ONRSPQRYSTOCKDISPOSAL 82
#define ONRSPQRYSTOCKDISPOSALACTION 83
#define ONRSPQRYCONDORDER 84
#define ONRSPQRYCONDORDERACTION 85
#define ONRSPQRYINVESTORLIMITPOSITION 86
#define ONRSPQRYINVESTORLIMITAMOUNT 87
#define ONRSPQRYCOMBORDERACTION 88
#define ONRSPQRYCOMBORDER 89
#define ONRSPQRYCOMBPOSITION 90
#define ONRSPQRYCOMBPOSDETAIL 91
#define ONRSPQRYEXERCISEAPPOINTMENT 92
#define ONRSPQRYINSUFFICIENTCOVEREDSTOCKPOSITION 93
#define ONRSPQRYCOMBSECURITY 94
#define ONRSPQRYCOMBEXERCISE 95
#define ONRSPQRYCOMBEXERCISEACTION 96


///-------------------------------------------------------------------------------------
///C++ SPI�Ļص���������ʵ��
///-------------------------------------------------------------------------------------

//API�ļ̳�ʵ��
class OptionApi : public CTORATstpSPTraderSpi
{
private:
	SPTRADER_API_DLL_EXPORT CTORATstpSPTraderApi* api;      //API����
	bool active = false;                //����״̬
	thread task_thread;                    //�����߳�ָ�루��python���������ݣ�
	TaskQueue task_queue;                //�������
	bool logging = false;


public:
	OptionApi()
	{
	};

	~OptionApi()
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
	virtual void OnRspError(CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	///��ȡ������ϢӦ��
	virtual void OnRspGetConnectionInfo(CTORATstpSPConnectionInfoField* pConnectionInfoField, CTORATstpSPRspInfoField* pRspInfoField, int nRequestID);


	//��¼Ӧ��
	virtual void OnRspUserLogin(CTORATstpSPRspUserLoginField* pRspUserLoginField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ǳ�Ӧ��
	virtual void OnRspUserLogout(CTORATstpSPUserLogoutField* pUserLogoutField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�޸�����Ӧ��
	virtual void OnRspUserPasswordUpdate(CTORATstpSPUserPasswordUpdateField* pUserPasswordUpdateField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����¼���豸����Ӧ��
	virtual void OnRspInputDeviceSerial(CTORATstpSPRspInputDeviceSerialField* pRspInputDeviceSerialField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����¼��Ӧ��
	virtual void OnRspOrderInsert(CTORATstpSPInputOrderField* pInputOrderField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�����ر�
	virtual void OnRtnOrder(CTORATstpSPOrderField* pOrder);

	//��������ر�
	virtual void OnErrRtnOrderInsert(CTORATstpSPInputOrderField* pInputOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����Ӧ��
	virtual void OnRspOrderAction(CTORATstpSPInputOrderActionField* pInputOrderActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��������ر�
	virtual void OnErrRtnOrderAction(CTORATstpSPInputOrderActionField* pInputOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ɽ��ر�
	virtual void OnRtnTrade(CTORATstpSPTradeField* pTrade);

	//��Ȩ������Ӧ
	virtual void OnRspExerciseInsert(CTORATstpSPInputExerciseField* pInputExerciseField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��Ȩ�ر�
	virtual void OnRtnExercise(CTORATstpSPExerciseField* pExercise);

	//��Ȩ�������ر�
	virtual void OnErrRtnExerciseInsert(CTORATstpSPInputExerciseField* pInputExercise, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��Ȩ������Ӧ
	virtual void OnRspExerciseAction(CTORATstpSPInputExerciseActionField* pInputExerciseActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��Ȩ��������ر�
	virtual void OnErrRtnExerciseAction(CTORATstpSPInputExerciseActionField* pInputExerciseAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����¼��������Ӧ
	virtual void OnRspLockInsert(CTORATstpSPInputLockField* pInputLockField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����֪ͨ
	virtual void OnRtnLock(CTORATstpSPLockField* pLock);

	//����¼�����ر�
	virtual void OnErrRtnLockInsert(CTORATstpSPInputLockField* pInputLock, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����������Ӧ
	virtual void OnRspLockAction(CTORATstpSPInputLockActionField* pInputLockActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//������������ر�
	virtual void OnErrRtnLockAction(CTORATstpSPInputLockActionField* pInputLockAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//֤ȯ���ûر�
	virtual void OnRtnStockDisposal(CTORATstpSPStockDisposalField* pStockDisposal);

	//���ί��¼��������Ӧ
	virtual void OnRspCombOrderInsert(CTORATstpSPInputCombOrderField* pInputCombOrderField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//���ί�лر�
	virtual void OnRtnCombOrder(CTORATstpSPCombOrderField* pCombOrder);

	//���ί���������ر�
	virtual void OnErrRtnCombOrderInsert(CTORATstpSPInputCombOrderField* pInputCombOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//���ί�в�����Ӧ
	virtual void OnRspCombOrderAction(CTORATstpSPInputCombOrderActionField* pInputCombOrderActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//���ί�в�������ر�
	virtual void OnErrRtnCombOrderAction(CTORATstpSPInputCombOrderActionField* pInputCombOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//������¼��������Ӧ
	virtual void OnRspCondOrderInsert(CTORATstpSPInputCondOrderField* pInputCondOrderField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�������ر�
	virtual void OnRtnCondOrder(CTORATstpSPConditionOrderField* pConditionOrder);

	//����������ر�
	virtual void OnErrRtnCondOrderInsert(CTORATstpSPInputCondOrderField* pInputCondOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//����������Ӧ��
	virtual void OnRspCondOrderAction(CTORATstpSPInputCondOrderActionField* pInputCondOrderActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��������������ر�
	virtual void OnErrRtnCondOrderAction(CTORATstpSPInputCondOrderActionField* pInputCondOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ϲ���Ȩ������Ӧ
	virtual void OnRspCombExerciseInsert(CTORATstpSPInputCombExerciseField* pInputCombExerciseField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ϲ���Ȩ�ر�
	virtual void OnRtnCombExercise(CTORATstpSPCombExerciseField* pCombExercise);

	//�ϲ���Ȩ�������ر�
	virtual void OnErrRtnCombExerciseInsert(CTORATstpSPInputCombExerciseField* pInputCombExercise, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ϲ���Ȩ������Ӧ
	virtual void OnRspCombExerciseAction(CTORATstpSPInputCombExerciseActionField* pInputCombExerciseActionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ϲ���Ȩ��������ر�
	virtual void OnErrRtnCombExerciseAction(CTORATstpSPInputCombExerciseActionField* pInputCombExerciseAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ��������������Ӧ
	virtual void OnRspInquiryMaxLockVolume(CTORATstpSPRspInquiryMaxLockVolumeField* pRspInquiryMaxLockVolumeField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ���ɱ����ֻ�������Ӧ
	virtual void OnRspInquiryMaxCoverVolume(CTORATstpSPRspInquiryMaxCoverVolumeField* pRspInquiryMaxCoverVolumeField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ�����Ϻ�Լ��֤����䶯������Ӧ
	virtual void OnRspInquirySplitCombMarginDifference(CTORATstpSPRspInquirySplitCombMarginDifferenceField* pRspInquirySplitCombMarginDifferenceField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ʽ�ת������Ӧ��
	virtual void OnRspTransferFund(CTORATstpSPInputTransferFundField* pInputTransferFundField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ʽ�ת�ƻر�
	virtual void OnRtnTransferFund(CTORATstpSPTransferFundField* pTransferFund);

	//�ʽ�ת�ƴ���ر�
	virtual void OnErrRtnTransferFund(CTORATstpSPInputTransferFundField* pInputTransferFund, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��λת�ƻر�
	virtual void OnRtnTransferPosition(CTORATstpSPTransferPositionField* pTransferPosition);

	//��λת�ƴ���ر�
	virtual void OnErrRtnTransferPosition(CTORATstpSPInputTransferPositionField* pInputTransferPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ֻ���λת��������Ӧ
	virtual void OnRspTransferStockPosition(CTORATstpSPInputTransferStockPositionField* pInputTransferStockPositionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�ֻ���λת�ƻر�
	virtual void OnRtnTransferStockPosition(CTORATstpSPTransferStockPositionField* pTransferStockPosition);

	//�ֻ���λת�ƴ���ر�
	virtual void OnErrRtnTransferStockPosition(CTORATstpSPInputTransferStockPositionField* pInputTransferStockPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ���н���ϵͳ�ʽ���Ӧ
	virtual void OnRspInquiryJZFund(CTORATstpSPRspInquiryJZFundField* pRspInquiryJZFundField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ�����˻������Ӧ
	virtual void OnRspInquiryBankAccountFund(CTORATstpSPRspInquiryBankAccountFundField* pRspInquiryBankAccountFundField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//��ѯ�ֻ�ϵͳ�ֻ��ֲ���Ӧ
	virtual void OnRspInquiryStockPosition(CTORATstpSPRspInquiryStockPositionField* pRspInquiryStockPositionField, CTORATstpSPRspInfoField* pRspInfo, int nRequestID);

	//�г�״̬֪ͨ
	virtual void OnRtnMarketStatus(CTORATstpSPMarketStatusField* pMarketStatus);

	//����֪ͨ�ر�
	virtual void OnRtnTradingNotice(CTORATstpSPTradingNoticeField* pTradingNotice);

	//��ѯ������
	virtual void OnRspQryExchange(CTORATstpSPExchangeField* pExchange, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯʵʱ����
	virtual void OnRspQryMarketData(CTORATstpSPMarketDataField* pMarketData, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ֤ȯ��Ϣ
	virtual void OnRspQrySecurity(CTORATstpSPSecurityField* pSecurity, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�����ϵ
	virtual void OnRspQryBUProxy(CTORATstpSPBUProxyField* pBUProxy, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯUser
	virtual void OnRspQryUser(CTORATstpSPUserField* pUser, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯͶ����
	virtual void OnRspQryInvestor(CTORATstpSPInvestorField* pInvestor, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ɶ��˻�
	virtual void OnRspQryShareholderAccount(CTORATstpSPShareholderAccountField* pShareholderAccount, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//�ʽ��˻���ѯ
	virtual void OnRspQryTradingAccount(CTORATstpSPTradingAccountField* pTradingAccount, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//������ѯ
	virtual void OnRspQryOrder(CTORATstpSPOrderField* pOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//�ɽ���ѯ
	virtual void OnRspQryTrade(CTORATstpSPTradeField* pTrade, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//Ͷ���ֲֲ߳�ѯ
	virtual void OnRspQryPosition(CTORATstpSPPositionField* pPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�������׷���
	virtual void OnRspQryTradingFee(CTORATstpSPTradingFeeField* pTradingFee, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯӶ�����
	virtual void OnRspQryInvestorTradingFee(CTORATstpSPInvestorTradingFeeField* pInvestorTradingFee, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��֤�����
	virtual void OnRspQryInvestorMarginFee(CTORATstpSPInvestorMarginFeeField* pInvestorMarginFee, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//������ϸ�ʽ��ѯ
	virtual void OnRspQryOrderFundDetail(CTORATstpSPOrderFundDetailField* pOrderFundDetail, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ʽ�ת����ˮ
	virtual void OnRspQryFundTransferDetail(CTORATstpSPFundTransferDetailField* pFundTransferDetail, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ֲ�ת����ˮ
	virtual void OnRspQryPositionTransferDetail(CTORATstpSPPositionTransferDetailField* pPositionTransferDetail, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ����
	virtual void OnRspQryOrderAction(CTORATstpSPOrderActionField* pOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ֻ��ֲ�
	virtual void OnRspQryStockPosition(CTORATstpSPStockPositionField* pStockPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ����ί��
	virtual void OnRspQryLock(CTORATstpSPLockField* pLock, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��Ȩί��
	virtual void OnRspQryExercise(CTORATstpSPExerciseField* pExercise, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�����ֲ�
	virtual void OnRspQryLockPosition(CTORATstpSPLockPositionField* pLockPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��Ȩ����
	virtual void OnRspQryExerciseAction(CTORATstpSPExerciseActionField* pExerciseAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��������
	virtual void OnRspQryLockAction(CTORATstpSPLockActionField* pLockAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��ĳֲ�ת����ϸ
	virtual void OnRspQryStockPositionTransferDetail(CTORATstpSPStockPositionTransferDetailField* pStockPositionTransferDetail, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ����֪ͨ
	virtual void OnRspQryTradingNotice(CTORATstpSPTradingNoticeField* pTradingNotice, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ֤ȯ����
	virtual void OnRspQryStockDisposal(CTORATstpSPStockDisposalField* pStockDisposal, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ֤ȯ���ó���
	virtual void OnRspQryStockDisposalAction(CTORATstpSPStockDisposalActionField* pStockDisposalAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ������
	virtual void OnRspQryCondOrder(CTORATstpSPCondOrderField* pCondOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ����������
	virtual void OnRspQryCondOrderAction(CTORATstpSPCondOrderActionField* pCondOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯͶ�����޲�
	virtual void OnRspQryInvestorLimitPosition(CTORATstpSPInvestorLimitPositionField* pInvestorLimitPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯͶ�����޶�
	virtual void OnRspQryInvestorLimitAmount(CTORATstpSPInvestorLimitAmountField* pInvestorLimitAmount, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��ϳ���
	virtual void OnRspQryCombOrderAction(CTORATstpSPCombOrderActionField* pCombOrderAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��ϱ���
	virtual void OnRspQryCombOrder(CTORATstpSPCombOrderField* pCombOrder, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��ϳֲ�
	virtual void OnRspQryCombPosition(CTORATstpSPCombPositionField* pCombPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��ϳֲ���ϸ
	virtual void OnRspQryCombPosDetail(CTORATstpSPCombPosDetailField* pCombPosDetail, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯͶ������Ȩָ����ϸ
	virtual void OnRspQryExerciseAppointment(CTORATstpSPExerciseAppointmentField* pExerciseAppointment, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ���ҹɷݲ����λ
	virtual void OnRspQryInsufficientCoveredStockPosition(CTORATstpSPInsufficientCoveredStockPositionField* pInsufficientCoveredStockPosition, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ��Ϻ�Լ��Ϣ
	virtual void OnRspQryCombSecurity(CTORATstpSPCombSecurityField* pCombSecurity, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ϲ���Ȩί��
	virtual void OnRspQryCombExercise(CTORATstpSPCombExerciseField* pCombExercise, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

	//��ѯ�ϲ���Ȩ����
	virtual void OnRspQryCombExerciseAction(CTORATstpSPCombExerciseActionField* pCombExerciseAction, CTORATstpSPRspInfoField* pRspInfo, int nRequestID, bool bIsLast);

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

	virtual void onRspOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTrade(const dict& data) {};

	virtual void onRspExerciseInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnExercise(const dict& data) {};

	virtual void onErrRtnExerciseInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspExerciseAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnExerciseAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspLockInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnLock(const dict& data) {};

	virtual void onErrRtnLockInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspLockAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnLockAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnStockDisposal(const dict& data) {};

	virtual void onRspCombOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnCombOrder(const dict& data) {};

	virtual void onErrRtnCombOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCombOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnCombOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCondOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnCondOrder(const dict& data) {};

	virtual void onErrRtnCondOrderInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCondOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnCondOrderAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCombExerciseInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnCombExercise(const dict& data) {};

	virtual void onErrRtnCombExerciseInsert(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspCombExerciseAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onErrRtnCombExerciseAction(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryMaxLockVolume(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryMaxCoverVolume(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquirySplitCombMarginDifference(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspTransferFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTransferFund(const dict& data) {};

	virtual void onErrRtnTransferFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTransferPosition(const dict& data) {};

	virtual void onErrRtnTransferPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspTransferStockPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnTransferStockPosition(const dict& data) {};

	virtual void onErrRtnTransferStockPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryJZFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryBankAccountFund(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRspInquiryStockPosition(const dict& data, const dict& error, int nRequestID) {};

	virtual void onRtnMarketStatus(const dict& data) {};

	virtual void onRtnTradingNotice(const dict& data) {};

	virtual void onRspQryExchange(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryMarketData(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQrySecurity(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryBUProxy(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryUser(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestor(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryShareholderAccount(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingAccount(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTrade(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingFee(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorTradingFee(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorMarginFee(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrderFundDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryFundTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryPositionTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryStockPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryLock(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryExercise(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryLockPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryExerciseAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryLockAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryStockPositionTransferDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryTradingNotice(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryStockDisposal(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryStockDisposalAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCondOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCondOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorLimitPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInvestorLimitAmount(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombOrderAction(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombOrder(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombPosDetail(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryExerciseAppointment(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryInsufficientCoveredStockPosition(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombSecurity(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombExercise(const dict& data, const dict& error, int nRequestID, bool last) {};

	virtual void onRspQryCombExerciseAction(const dict& data, const dict& error, int nRequestID, bool last) {};

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

	void processRspOrderAction(Task* task);

	void processErrRtnOrderAction(Task* task);

	void processRtnTrade(Task* task);

	void processRspExerciseInsert(Task* task);

	void processRtnExercise(Task* task);

	void processErrRtnExerciseInsert(Task* task);

	void processRspExerciseAction(Task* task);

	void processErrRtnExerciseAction(Task* task);

	void processRspLockInsert(Task* task);

	void processRtnLock(Task* task);

	void processErrRtnLockInsert(Task* task);

	void processRspLockAction(Task* task);

	void processErrRtnLockAction(Task* task);

	void processRtnStockDisposal(Task* task);

	void processRspCombOrderInsert(Task* task);

	void processRtnCombOrder(Task* task);

	void processErrRtnCombOrderInsert(Task* task);

	void processRspCombOrderAction(Task* task);

	void processErrRtnCombOrderAction(Task* task);

	void processRspCondOrderInsert(Task* task);

	void processRtnCondOrder(Task* task);

	void processErrRtnCondOrderInsert(Task* task);

	void processRspCondOrderAction(Task* task);

	void processErrRtnCondOrderAction(Task* task);

	void processRspCombExerciseInsert(Task* task);

	void processRtnCombExercise(Task* task);

	void processErrRtnCombExerciseInsert(Task* task);

	void processRspCombExerciseAction(Task* task);

	void processErrRtnCombExerciseAction(Task* task);

	void processRspInquiryMaxLockVolume(Task* task);

	void processRspInquiryMaxCoverVolume(Task* task);

	void processRspInquirySplitCombMarginDifference(Task* task);

	void processRspTransferFund(Task* task);

	void processRtnTransferFund(Task* task);

	void processErrRtnTransferFund(Task* task);

	void processRtnTransferPosition(Task* task);

	void processErrRtnTransferPosition(Task* task);

	void processRspTransferStockPosition(Task* task);

	void processRtnTransferStockPosition(Task* task);

	void processErrRtnTransferStockPosition(Task* task);

	void processRspInquiryJZFund(Task* task);

	void processRspInquiryBankAccountFund(Task* task);

	void processRspInquiryStockPosition(Task* task);

	void processRtnMarketStatus(Task* task);

	void processRtnTradingNotice(Task* task);

	void processRspQryExchange(Task* task);

	void processRspQryMarketData(Task* task);

	void processRspQrySecurity(Task* task);

	void processRspQryBUProxy(Task* task);

	void processRspQryUser(Task* task);

	void processRspQryInvestor(Task* task);

	void processRspQryShareholderAccount(Task* task);

	void processRspQryTradingAccount(Task* task);

	void processRspQryOrder(Task* task);

	void processRspQryTrade(Task* task);

	void processRspQryPosition(Task* task);

	void processRspQryTradingFee(Task* task);

	void processRspQryInvestorTradingFee(Task* task);

	void processRspQryInvestorMarginFee(Task* task);

	void processRspQryOrderFundDetail(Task* task);

	void processRspQryFundTransferDetail(Task* task);

	void processRspQryPositionTransferDetail(Task* task);

	void processRspQryOrderAction(Task* task);

	void processRspQryStockPosition(Task* task);

	void processRspQryLock(Task* task);

	void processRspQryExercise(Task* task);

	void processRspQryLockPosition(Task* task);

	void processRspQryExerciseAction(Task* task);

	void processRspQryLockAction(Task* task);

	void processRspQryStockPositionTransferDetail(Task* task);

	void processRspQryTradingNotice(Task* task);

	void processRspQryStockDisposal(Task* task);

	void processRspQryStockDisposalAction(Task* task);

	void processRspQryCondOrder(Task* task);

	void processRspQryCondOrderAction(Task* task);

	void processRspQryInvestorLimitPosition(Task* task);

	void processRspQryInvestorLimitAmount(Task* task);

	void processRspQryCombOrderAction(Task* task);

	void processRspQryCombOrder(Task* task);

	void processRspQryCombPosition(Task* task);

	void processRspQryCombPosDetail(Task* task);

	void processRspQryExerciseAppointment(Task* task);

	void processRspQryInsufficientCoveredStockPosition(Task* task);

	void processRspQryCombSecurity(Task* task);

	void processRspQryCombExercise(Task* task);

	void processRspQryCombExerciseAction(Task* task);

	//-------------------------------------------------------------------------------------
	//req:���������������ֵ�
	//-------------------------------------------------------------------------------------

	void createTstpSPTraderApi(string pszFlowPath, bool bEncrypt);

	void registerFront(string pszFrontAddress);

	void init();

	int join();

	void release();

	string getApiVersion();

	int exit();

	void registerNameServer(string pszNsAddress);

	void subscribePrivateTopic(int type);

	void subscribePublicTopic(int type);

	int reqGetConnectionInfo(int nrequestid);

	int reqUserLogin(const dict& req, int nrequestid);

	int reqUserLogout(const dict& req, int nrequestid);

	int reqUserPasswordUpdate(const dict& req, int nrequestid);

	int reqInputDeviceSerial(const dict& req, int nrequestid);

	int reqOrderInsert(const dict& req, int nrequestid);

	int reqOrderAction(const dict& req, int nrequestid);

	int reqExerciseInsert(const dict& req, int nrequestid);

	int reqExerciseAction(const dict& req, int nrequestid);

	int reqLockInsert(const dict& req, int nrequestid);

	int reqLockAction(const dict& req, int nrequestid);

	int reqCombOrderInsert(const dict& req, int nrequestid);

	int reqCombOrderAction(const dict& req, int nrequestid);

	int reqCondOrderInsert(const dict& req, int nrequestid);

	int reqCondOrderAction(const dict& req, int nrequestid);

	int reqCombExerciseInsert(const dict& req, int nrequestid);

	int reqCombExerciseAction(const dict& req, int nrequestid);

	int reqInquiryMaxLockVolume(const dict& req, int nrequestid);

	int reqInquiryMaxCoverVolume(const dict& req, int nrequestid);

	int reqInquirySplitCombMarginDifference(const dict& req, int nrequestid);

	int reqTransferFund(const dict& req, int nrequestid);

	int reqTransferStockPosition(const dict& req, int nrequestid);

	int reqInquiryJZFund(const dict& req, int nrequestid);

	int reqInquiryBankAccountFund(const dict& req, int nrequestid);

	int reqInquiryStockPosition(const dict& req, int nrequestid);

	int reqQryExchange(const dict& req, int nrequestid);

	int reqQryMarketData(const dict& req, int nrequestid);

	int reqQrySecurity(const dict& req, int nrequestid);

	int reqQryBUProxy(const dict& req, int nrequestid);

	int reqQryUser(const dict& req, int nrequestid);

	int reqQryInvestor(const dict& req, int nrequestid);

	int reqQryShareholderAccount(const dict& req, int nrequestid);

	int reqQryTradingAccount(const dict& req, int nrequestid);

	int reqQryOrder(const dict& req, int nrequestid);

	int reqQryTrade(const dict& req, int nrequestid);

	int reqQryPosition(const dict& req, int nrequestid);

	int reqQryTradingFee(const dict& req, int nrequestid);

	int reqQryInvestorTradingFee(const dict& req, int nrequestid);

	int reqQryInvestorMarginFee(const dict& req, int nrequestid);

	int reqQryOrderFundDetail(const dict& req, int nrequestid);

	int reqQryFundTransferDetail(const dict& req, int nrequestid);

	int reqQryPositionTransferDetail(const dict& req, int nrequestid);

	int reqQryOrderAction(const dict& req, int nrequestid);

	int reqQryStockPosition(const dict& req, int nrequestid);

	int reqQryLock(const dict& req, int nrequestid);

	int reqQryExercise(const dict& req, int nrequestid);

	int reqQryLockPosition(const dict& req, int nrequestid);

	int reqQryExerciseAction(const dict& req, int nrequestid);

	int reqQryLockAction(const dict& req, int nrequestid);

	int reqQryStockPositionTransferDetail(const dict& req, int nrequestid);

	int reqQryTradingNotice(const dict& req, int nrequestid);

	int reqQryStockDisposal(const dict& req, int nrequestid);

	int reqQryStockDisposalAction(const dict& req, int nrequestid);

	int reqQryCondOrder(const dict& req, int nrequestid);

	int reqQryCondOrderAction(const dict& req, int nrequestid);

	int reqQryInvestorLimitPosition(const dict& req, int nrequestid);

	int reqQryInvestorLimitAmount(const dict& req, int nrequestid);

	int reqQryCombOrderAction(const dict& req, int nrequestid);

	int reqQryCombOrder(const dict& req, int nrequestid);

	int reqQryCombPosition(const dict& req, int nrequestid);

	int reqQryCombPosDetail(const dict& req, int nrequestid);

	int reqQryExerciseAppointment(const dict& req, int nrequestid);

	int reqQryInsufficientCoveredStockPosition(const dict& req, int nrequestid);

	int reqQryCombSecurity(const dict& req, int nrequestid);

	int reqQryCombExercise(const dict& req, int nrequestid);

	int reqQryCombExerciseAction(const dict& req, int nrequestid);
};
