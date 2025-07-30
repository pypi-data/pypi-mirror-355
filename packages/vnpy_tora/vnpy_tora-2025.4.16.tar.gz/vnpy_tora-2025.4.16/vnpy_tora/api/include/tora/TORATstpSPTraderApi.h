/////////////////////////////////////////////////////////////////////////
///@company �Ϻ�̩����Ϣ�Ƽ����޹�˾
///@file TORATstpSPTraderApi.h
///@brief �����˿ͻ��˽ӿ�
///@history 
/////////////////////////////////////////////////////////////////////////

#ifndef _TORA_TSTPSPTRADERAPI_H
#define _TORA_TSTPSPTRADERAPI_H

#include "TORATstpSPUserApiStruct.h"

#ifdef SPTRADER_API_EXPORT
#ifdef WINDOWS
#define SPTRADER_API_DLL_EXPORT __declspec(dllexport)
#else
#define SPTRADER_API_DLL_EXPORT __attribute__ ((visibility("default")))
#endif
#else
#define SPTRADER_API_DLL_EXPORT 
#endif

namespace TORASPAPI
{
	class CTORATstpSPTraderSpi
	{
	public:
		///���ͻ����뽻�׺�̨������ͨ������ʱ����δ��¼ǰ�����÷��������á�
		virtual void OnFrontConnected(){};
		
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
		virtual void OnFrontDisconnected(int nReason){};
			
		///����Ӧ��
		virtual void OnRspError(CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {};
		
		///��ȡ������ϢӦ��
		virtual void OnRspGetConnectionInfo(CTORATstpSPConnectionInfoField *pConnectionInfoField, CTORATstpSPRspInfoField *pRspInfoField, int nRequestID) {};
		
		
		//��¼Ӧ��
		virtual void OnRspUserLogin(CTORATstpSPRspUserLoginField *pRspUserLoginField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ǳ�Ӧ��
		virtual void OnRspUserLogout(CTORATstpSPUserLogoutField *pUserLogoutField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�޸�����Ӧ��
		virtual void OnRspUserPasswordUpdate(CTORATstpSPUserPasswordUpdateField *pUserPasswordUpdateField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//����¼���豸����Ӧ��
		virtual void OnRspInputDeviceSerial(CTORATstpSPRspInputDeviceSerialField *pRspInputDeviceSerialField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//����¼��Ӧ��
		virtual void OnRspOrderInsert(CTORATstpSPInputOrderField *pInputOrderField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�����ر�
		virtual void OnRtnOrder(CTORATstpSPOrderField *pOrder) {};
		
		//��������ر�
		virtual void OnErrRtnOrderInsert(CTORATstpSPInputOrderField *pInputOrder, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//����Ӧ��
		virtual void OnRspOrderAction(CTORATstpSPInputOrderActionField *pInputOrderActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��������ر�
		virtual void OnErrRtnOrderAction(CTORATstpSPInputOrderActionField *pInputOrderAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//�ɽ��ر�
		virtual void OnRtnTrade(CTORATstpSPTradeField *pTrade) {};
		
		//��Ȩ������Ӧ
		virtual void OnRspExerciseInsert(CTORATstpSPInputExerciseField *pInputExerciseField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��Ȩ�ر�
		virtual void OnRtnExercise(CTORATstpSPExerciseField *pExercise) {};
		
		//��Ȩ�������ر�
		virtual void OnErrRtnExerciseInsert(CTORATstpSPInputExerciseField *pInputExercise, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//��Ȩ������Ӧ
		virtual void OnRspExerciseAction(CTORATstpSPInputExerciseActionField *pInputExerciseActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��Ȩ��������ر�
		virtual void OnErrRtnExerciseAction(CTORATstpSPInputExerciseActionField *pInputExerciseAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//����¼��������Ӧ
		virtual void OnRspLockInsert(CTORATstpSPInputLockField *pInputLockField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//����֪ͨ
		virtual void OnRtnLock(CTORATstpSPLockField *pLock) {};
		
		//����¼�����ر�
		virtual void OnErrRtnLockInsert(CTORATstpSPInputLockField *pInputLock, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//����������Ӧ
		virtual void OnRspLockAction(CTORATstpSPInputLockActionField *pInputLockActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//������������ر�
		virtual void OnErrRtnLockAction(CTORATstpSPInputLockActionField *pInputLockAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//֤ȯ���ûر�
		virtual void OnRtnStockDisposal(CTORATstpSPStockDisposalField *pStockDisposal) {};
		
		//���ί��¼��������Ӧ
		virtual void OnRspCombOrderInsert(CTORATstpSPInputCombOrderField *pInputCombOrderField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//���ί�лر�
		virtual void OnRtnCombOrder(CTORATstpSPCombOrderField *pCombOrder) {};
		
		//���ί���������ر�
		virtual void OnErrRtnCombOrderInsert(CTORATstpSPInputCombOrderField *pInputCombOrder, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//���ί�в�����Ӧ
		virtual void OnRspCombOrderAction(CTORATstpSPInputCombOrderActionField *pInputCombOrderActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//���ί�в�������ر�
		virtual void OnErrRtnCombOrderAction(CTORATstpSPInputCombOrderActionField *pInputCombOrderAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//������¼��������Ӧ
		virtual void OnRspCondOrderInsert(CTORATstpSPInputCondOrderField *pInputCondOrderField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�������ر�
		virtual void OnRtnCondOrder(CTORATstpSPConditionOrderField *pConditionOrder) {};
		
		//����������ر�
		virtual void OnErrRtnCondOrderInsert(CTORATstpSPInputCondOrderField *pInputCondOrder, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//����������Ӧ��
		virtual void OnRspCondOrderAction(CTORATstpSPInputCondOrderActionField *pInputCondOrderActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��������������ر�
		virtual void OnErrRtnCondOrderAction(CTORATstpSPInputCondOrderActionField *pInputCondOrderAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//�ϲ���Ȩ������Ӧ
		virtual void OnRspCombExerciseInsert(CTORATstpSPInputCombExerciseField *pInputCombExerciseField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ϲ���Ȩ�ر�
		virtual void OnRtnCombExercise(CTORATstpSPCombExerciseField *pCombExercise) {};
		
		//�ϲ���Ȩ�������ر�
		virtual void OnErrRtnCombExerciseInsert(CTORATstpSPInputCombExerciseField *pInputCombExercise, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//�ϲ���Ȩ������Ӧ
		virtual void OnRspCombExerciseAction(CTORATstpSPInputCombExerciseActionField *pInputCombExerciseActionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ϲ���Ȩ��������ر�
		virtual void OnErrRtnCombExerciseAction(CTORATstpSPInputCombExerciseActionField *pInputCombExerciseAction, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//��ѯ��������������Ӧ
		virtual void OnRspInquiryMaxLockVolume(CTORATstpSPRspInquiryMaxLockVolumeField *pRspInquiryMaxLockVolumeField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��ѯ���ɱ����ֻ�������Ӧ
		virtual void OnRspInquiryMaxCoverVolume(CTORATstpSPRspInquiryMaxCoverVolumeField *pRspInquiryMaxCoverVolumeField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��ѯ�����Ϻ�Լ��֤����䶯������Ӧ
		virtual void OnRspInquirySplitCombMarginDifference(CTORATstpSPRspInquirySplitCombMarginDifferenceField *pRspInquirySplitCombMarginDifferenceField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ʽ�ת������Ӧ��
		virtual void OnRspTransferFund(CTORATstpSPInputTransferFundField *pInputTransferFundField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ʽ�ת�ƻر�
		virtual void OnRtnTransferFund(CTORATstpSPTransferFundField *pTransferFund) {};
		
		//�ʽ�ת�ƴ���ر�
		virtual void OnErrRtnTransferFund(CTORATstpSPInputTransferFundField *pInputTransferFund, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//��λת�ƻر�
		virtual void OnRtnTransferPosition(CTORATstpSPTransferPositionField *pTransferPosition) {};
		
		//��λת�ƴ���ر�
		virtual void OnErrRtnTransferPosition(CTORATstpSPInputTransferPositionField *pInputTransferPosition, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//�ֻ���λת��������Ӧ
		virtual void OnRspTransferStockPosition(CTORATstpSPInputTransferStockPositionField *pInputTransferStockPositionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�ֻ���λת�ƻر�
		virtual void OnRtnTransferStockPosition(CTORATstpSPTransferStockPositionField *pTransferStockPosition) {};
		
		//�ֻ���λת�ƴ���ر�
		virtual void OnErrRtnTransferStockPosition(CTORATstpSPInputTransferStockPositionField *pInputTransferStockPosition, CTORATstpSPRspInfoField *pRspInfo,int nRequestID) {};
		
		//��ѯ���н���ϵͳ�ʽ���Ӧ
		virtual void OnRspInquiryJZFund(CTORATstpSPRspInquiryJZFundField *pRspInquiryJZFundField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��ѯ�����˻������Ӧ
		virtual void OnRspInquiryBankAccountFund(CTORATstpSPRspInquiryBankAccountFundField *pRspInquiryBankAccountFundField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//��ѯ�ֻ�ϵͳ�ֻ��ֲ���Ӧ
		virtual void OnRspInquiryStockPosition(CTORATstpSPRspInquiryStockPositionField *pRspInquiryStockPositionField, CTORATstpSPRspInfoField *pRspInfo, int nRequestID) {};
		
		//�г�״̬֪ͨ
		virtual void OnRtnMarketStatus(CTORATstpSPMarketStatusField *pMarketStatus) {};
		
		//����֪ͨ�ر�
		virtual void OnRtnTradingNotice(CTORATstpSPTradingNoticeField *pTradingNotice) {};
		
		//��ѯ������
		virtual void OnRspQryExchange(CTORATstpSPExchangeField *pExchange, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯʵʱ����
		virtual void OnRspQryMarketData(CTORATstpSPMarketDataField *pMarketData, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ֤ȯ��Ϣ
		virtual void OnRspQrySecurity(CTORATstpSPSecurityField *pSecurity, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�����ϵ
		virtual void OnRspQryBUProxy(CTORATstpSPBUProxyField *pBUProxy, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯUser
		virtual void OnRspQryUser(CTORATstpSPUserField *pUser, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯͶ����
		virtual void OnRspQryInvestor(CTORATstpSPInvestorField *pInvestor, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ɶ��˻�
		virtual void OnRspQryShareholderAccount(CTORATstpSPShareholderAccountField *pShareholderAccount, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//�ʽ��˻���ѯ
		virtual void OnRspQryTradingAccount(CTORATstpSPTradingAccountField *pTradingAccount, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//������ѯ
		virtual void OnRspQryOrder(CTORATstpSPOrderField *pOrder, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//�ɽ���ѯ
		virtual void OnRspQryTrade(CTORATstpSPTradeField *pTrade, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//Ͷ���ֲֲ߳�ѯ
		virtual void OnRspQryPosition(CTORATstpSPPositionField *pPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�������׷���
		virtual void OnRspQryTradingFee(CTORATstpSPTradingFeeField *pTradingFee, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯӶ�����
		virtual void OnRspQryInvestorTradingFee(CTORATstpSPInvestorTradingFeeField *pInvestorTradingFee, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��֤�����
		virtual void OnRspQryInvestorMarginFee(CTORATstpSPInvestorMarginFeeField *pInvestorMarginFee, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//������ϸ�ʽ��ѯ
		virtual void OnRspQryOrderFundDetail(CTORATstpSPOrderFundDetailField *pOrderFundDetail, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ʽ�ת����ˮ
		virtual void OnRspQryFundTransferDetail(CTORATstpSPFundTransferDetailField *pFundTransferDetail, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ֲ�ת����ˮ
		virtual void OnRspQryPositionTransferDetail(CTORATstpSPPositionTransferDetailField *pPositionTransferDetail, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ����
		virtual void OnRspQryOrderAction(CTORATstpSPOrderActionField *pOrderAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ֻ��ֲ�
		virtual void OnRspQryStockPosition(CTORATstpSPStockPositionField *pStockPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ����ί��
		virtual void OnRspQryLock(CTORATstpSPLockField *pLock, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��Ȩί��
		virtual void OnRspQryExercise(CTORATstpSPExerciseField *pExercise, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�����ֲ�
		virtual void OnRspQryLockPosition(CTORATstpSPLockPositionField *pLockPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��Ȩ����
		virtual void OnRspQryExerciseAction(CTORATstpSPExerciseActionField *pExerciseAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��������
		virtual void OnRspQryLockAction(CTORATstpSPLockActionField *pLockAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��ĳֲ�ת����ϸ
		virtual void OnRspQryStockPositionTransferDetail(CTORATstpSPStockPositionTransferDetailField *pStockPositionTransferDetail, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ����֪ͨ
		virtual void OnRspQryTradingNotice(CTORATstpSPTradingNoticeField *pTradingNotice, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ֤ȯ����
		virtual void OnRspQryStockDisposal(CTORATstpSPStockDisposalField *pStockDisposal, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ֤ȯ���ó���
		virtual void OnRspQryStockDisposalAction(CTORATstpSPStockDisposalActionField *pStockDisposalAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ������
		virtual void OnRspQryCondOrder(CTORATstpSPCondOrderField *pCondOrder, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ����������
		virtual void OnRspQryCondOrderAction(CTORATstpSPCondOrderActionField *pCondOrderAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯͶ�����޲�
		virtual void OnRspQryInvestorLimitPosition(CTORATstpSPInvestorLimitPositionField *pInvestorLimitPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯͶ�����޶�
		virtual void OnRspQryInvestorLimitAmount(CTORATstpSPInvestorLimitAmountField *pInvestorLimitAmount, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��ϳ���
		virtual void OnRspQryCombOrderAction(CTORATstpSPCombOrderActionField *pCombOrderAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��ϱ���
		virtual void OnRspQryCombOrder(CTORATstpSPCombOrderField *pCombOrder, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��ϳֲ�
		virtual void OnRspQryCombPosition(CTORATstpSPCombPositionField *pCombPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��ϳֲ���ϸ
		virtual void OnRspQryCombPosDetail(CTORATstpSPCombPosDetailField *pCombPosDetail, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯͶ������Ȩָ����ϸ
		virtual void OnRspQryExerciseAppointment(CTORATstpSPExerciseAppointmentField *pExerciseAppointment, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ���ҹɷݲ����λ
		virtual void OnRspQryInsufficientCoveredStockPosition(CTORATstpSPInsufficientCoveredStockPositionField *pInsufficientCoveredStockPosition, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ��Ϻ�Լ��Ϣ
		virtual void OnRspQryCombSecurity(CTORATstpSPCombSecurityField *pCombSecurity, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ϲ���Ȩί��
		virtual void OnRspQryCombExercise(CTORATstpSPCombExerciseField *pCombExercise, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
		
		//��ѯ�ϲ���Ȩ����
		virtual void OnRspQryCombExerciseAction(CTORATstpSPCombExerciseActionField *pCombExerciseAction, CTORATstpSPRspInfoField *pRspInfo, int nRequestID, bool bIsLast) {}; 
			
	};

	class SPTRADER_API_DLL_EXPORT CTORATstpSPTraderApi
	{
	public:
		///����TraderApi
		///@param pszFlowPath ����������Ϣ�ļ���Ŀ¼��Ĭ��Ϊ��ǰĿ¼
		///@param bEncrpyt ���������Ƿ���ܴ��䣬Ĭ�ϲ�����
		///@return ��������TraderApi
		static CTORATstpSPTraderApi *CreateTstpSPTraderApi(const char *pszFlowPath = "", bool bEncrypt = false);
		
		///��ȡAPI�汾��
		///@return �汾��
		static const char* GetApiVersion();
		
		///ɾ���ӿڶ�����
		///@remark ����ʹ�ñ��ӿڶ���ʱ,���øú���ɾ���ӿڶ���
		virtual void Release() = 0;
		
		///��ʼ��
		///@remark ��ʼ�����л���,ֻ�е��ú�,�ӿڲſ�ʼ����
		virtual void Init() = 0;
		
		///�ȴ��ӿ��߳̽�������
		///@return �߳��˳�����
		virtual int Join() = 0;
		
		///ע��ǰ�û������ַ
		///@param pszFrontAddress��ǰ�û������ַ��
		///@remark �����ַ�ĸ�ʽΪ����protocol://ipaddress:port�����磺��tcp://127.0.0.1:17001���� 
		///@remark ��tcp��������Э�飬��127.0.0.1�������������ַ����17001������������˿ںš�
		virtual void RegisterFront(char *pszFrontAddress) = 0;

		///ע�����ַ����������ַ
		///@param pszNsAddress�����ַ����������ַ��
		///@remark �����ַ�ĸ�ʽΪ����protocol://ipaddress:port�����磺��tcp://127.0.0.1:12001���� 
		///@remark ��tcp��������Э�飬��127.0.0.1�������������ַ����12001������������˿ںš�
		///@remark RegisterNameServer��RegisterFront��ѡ��һ��
		virtual void RegisterNameServer(char *pszNsAddress) = 0;

		///ע��ص��ӿ�
		///@param pSpi �����Իص��ӿ����ʵ��
		virtual void RegisterSpi(CTORATstpSPTraderSpi *pSpi) = 0;
		
		///����˽������
		///@param nResumeType ˽�����ش���ʽ  
		///        TORA_TERT_RESTART:�ӱ������տ�ʼ�ش�
		///        TORA_TERT_RESUME:���ϴ��յ�������
		///        TORA_TERT_QUICK:ֻ���͵�¼��˽����������
		///@remark �÷���Ҫ��Init����ǰ���á����������򲻻��յ�˽���������ݡ�
		virtual void SubscribePrivateTopic(TORA_TE_RESUME_TYPE nResumeType) = 0;
		
		///���Ĺ�������
		///@param nResumeType �������ش���ʽ  
		///        TORA_TERT_RESTART:�ӱ������տ�ʼ�ش�
		///        TORA_TERT_RESUME:���ϴ��յ�������
		///        TORA_TERT_QUICK:ֻ���͵�¼�󹫹���������
		///@remark �÷���Ҫ��Init����ǰ���á����������򲻻��յ������������ݡ�
		virtual void SubscribePublicTopic(TORA_TE_RESUME_TYPE nResumeType) = 0;
		
		///��ȡ������Ϣ
		virtual int ReqGetConnectionInfo(int nRequestID) = 0;
		
		
		//��¼����
		virtual int ReqUserLogin(CTORATstpSPReqUserLoginField *pReqUserLoginField, int nRequestID) = 0;
		
		//�ǳ�����
		virtual int ReqUserLogout(CTORATstpSPUserLogoutField *pUserLogoutField, int nRequestID) = 0;
		
		//�޸���������
		virtual int ReqUserPasswordUpdate(CTORATstpSPUserPasswordUpdateField *pUserPasswordUpdateField, int nRequestID) = 0;
		
		//����¼���豸����
		virtual int ReqInputDeviceSerial(CTORATstpSPReqInputDeviceSerialField *pReqInputDeviceSerialField, int nRequestID) = 0;
		
		//����¼������
		virtual int ReqOrderInsert(CTORATstpSPInputOrderField *pInputOrderField, int nRequestID) = 0;
		
		//��������
		virtual int ReqOrderAction(CTORATstpSPInputOrderActionField *pInputOrderActionField, int nRequestID) = 0;
		
		//��Ȩ����
		virtual int ReqExerciseInsert(CTORATstpSPInputExerciseField *pInputExerciseField, int nRequestID) = 0;
		
		//��Ȩ��������
		virtual int ReqExerciseAction(CTORATstpSPInputExerciseActionField *pInputExerciseActionField, int nRequestID) = 0;
		
		//����¼������
		virtual int ReqLockInsert(CTORATstpSPInputLockField *pInputLockField, int nRequestID) = 0;
		
		//������������
		virtual int ReqLockAction(CTORATstpSPInputLockActionField *pInputLockActionField, int nRequestID) = 0;
		
		//���ί��¼������
		virtual int ReqCombOrderInsert(CTORATstpSPInputCombOrderField *pInputCombOrderField, int nRequestID) = 0;
		
		//���ί�в�������
		virtual int ReqCombOrderAction(CTORATstpSPInputCombOrderActionField *pInputCombOrderActionField, int nRequestID) = 0;
		
		//������¼������
		virtual int ReqCondOrderInsert(CTORATstpSPInputCondOrderField *pInputCondOrderField, int nRequestID) = 0;
		
		//��������������
		virtual int ReqCondOrderAction(CTORATstpSPInputCondOrderActionField *pInputCondOrderActionField, int nRequestID) = 0;
		
		//�ϲ���Ȩ����
		virtual int ReqCombExerciseInsert(CTORATstpSPInputCombExerciseField *pInputCombExerciseField, int nRequestID) = 0;
		
		//�ϲ���Ȩ��������
		virtual int ReqCombExerciseAction(CTORATstpSPInputCombExerciseActionField *pInputCombExerciseActionField, int nRequestID) = 0;
		
		//��ѯ����������������
		virtual int ReqInquiryMaxLockVolume(CTORATstpSPReqInquiryMaxLockVolumeField *pReqInquiryMaxLockVolumeField, int nRequestID) = 0;
		
		//��ѯ���ɱ����ֻ���������
		virtual int ReqInquiryMaxCoverVolume(CTORATstpSPReqInquiryMaxCoverVolumeField *pReqInquiryMaxCoverVolumeField, int nRequestID) = 0;
		
		//��ѯ�����Ϻ�Լ��֤����䶯����
		virtual int ReqInquirySplitCombMarginDifference(CTORATstpSPReqInquirySplitCombMarginDifferenceField *pReqInquirySplitCombMarginDifferenceField, int nRequestID) = 0;
		
		//�ʽ�ת������
		virtual int ReqTransferFund(CTORATstpSPInputTransferFundField *pInputTransferFundField, int nRequestID) = 0;
		
		//�ֻ���λת������
		virtual int ReqTransferStockPosition(CTORATstpSPInputTransferStockPositionField *pInputTransferStockPositionField, int nRequestID) = 0;
		
		//��ѯ���н���ϵͳ�ʽ�����
		virtual int ReqInquiryJZFund(CTORATstpSPReqInquiryJZFundField *pReqInquiryJZFundField, int nRequestID) = 0;
		
		//��ѯ�����˻��������
		virtual int ReqInquiryBankAccountFund(CTORATstpSPReqInquiryBankAccountFundField *pReqInquiryBankAccountFundField, int nRequestID) = 0;
		
		//��ѯ�ֻ�ϵͳ�ֻ��ֲ�����
		virtual int ReqInquiryStockPosition(CTORATstpSPReqInquiryStockPositionField *pReqInquiryStockPositionField, int nRequestID) = 0;
		
		//��ѯ������
		virtual int ReqQryExchange(CTORATstpSPQryExchangeField *pQryExchangeField, int nRequestID) = 0;
		
		//��ѯʵʱ����
		virtual int ReqQryMarketData(CTORATstpSPQryMarketDataField *pQryMarketDataField, int nRequestID) = 0;
		
		//��ѯ֤ȯ��Ϣ
		virtual int ReqQrySecurity(CTORATstpSPQrySecurityField *pQrySecurityField, int nRequestID) = 0;
		
		//��ѯ�����ϵ
		virtual int ReqQryBUProxy(CTORATstpSPQryBUProxyField *pQryBUProxyField, int nRequestID) = 0;
		
		//��ѯUser
		virtual int ReqQryUser(CTORATstpSPQryUserField *pQryUserField, int nRequestID) = 0;
		
		//��ѯͶ����
		virtual int ReqQryInvestor(CTORATstpSPQryInvestorField *pQryInvestorField, int nRequestID) = 0;
		
		//��ѯ�ɶ��˻�
		virtual int ReqQryShareholderAccount(CTORATstpSPQryShareholderAccountField *pQryShareholderAccountField, int nRequestID) = 0;
		
		//�ʽ��˻���ѯ
		virtual int ReqQryTradingAccount(CTORATstpSPQryTradingAccountField *pQryTradingAccountField, int nRequestID) = 0;
		
		//������ѯ
		virtual int ReqQryOrder(CTORATstpSPQryOrderField *pQryOrderField, int nRequestID) = 0;
		
		//�ɽ���ѯ
		virtual int ReqQryTrade(CTORATstpSPQryTradeField *pQryTradeField, int nRequestID) = 0;
		
		//Ͷ���ֲֲ߳�ѯ
		virtual int ReqQryPosition(CTORATstpSPQryPositionField *pQryPositionField, int nRequestID) = 0;
		
		//��ѯ�������׷���
		virtual int ReqQryTradingFee(CTORATstpSPQryTradingFeeField *pQryTradingFeeField, int nRequestID) = 0;
		
		//��ѯӶ�����
		virtual int ReqQryInvestorTradingFee(CTORATstpSPQryInvestorTradingFeeField *pQryInvestorTradingFeeField, int nRequestID) = 0;
		
		//��ѯ��֤�����
		virtual int ReqQryInvestorMarginFee(CTORATstpSPQryInvestorMarginFeeField *pQryInvestorMarginFeeField, int nRequestID) = 0;
		
		//������ϸ�ʽ��ѯ
		virtual int ReqQryOrderFundDetail(CTORATstpSPQryOrderFundDetailField *pQryOrderFundDetailField, int nRequestID) = 0;
		
		//��ѯ�ʽ�ת����ˮ
		virtual int ReqQryFundTransferDetail(CTORATstpSPQryFundTransferDetailField *pQryFundTransferDetailField, int nRequestID) = 0;
		
		//��ѯ�ֲ�ת����ˮ
		virtual int ReqQryPositionTransferDetail(CTORATstpSPQryPositionTransferDetailField *pQryPositionTransferDetailField, int nRequestID) = 0;
		
		//��ѯ����
		virtual int ReqQryOrderAction(CTORATstpSPQryOrderActionField *pQryOrderActionField, int nRequestID) = 0;
		
		//��ѯ�ֻ��ֲ�
		virtual int ReqQryStockPosition(CTORATstpSPQryStockPositionField *pQryStockPositionField, int nRequestID) = 0;
		
		//��ѯ����ί��
		virtual int ReqQryLock(CTORATstpSPQryLockField *pQryLockField, int nRequestID) = 0;
		
		//��ѯ��Ȩί��
		virtual int ReqQryExercise(CTORATstpSPQryExerciseField *pQryExerciseField, int nRequestID) = 0;
		
		//��ѯ�����ֲ�
		virtual int ReqQryLockPosition(CTORATstpSPQryLockPositionField *pQryLockPositionField, int nRequestID) = 0;
		
		//��ѯ��Ȩ����
		virtual int ReqQryExerciseAction(CTORATstpSPQryExerciseActionField *pQryExerciseActionField, int nRequestID) = 0;
		
		//��ѯ��������
		virtual int ReqQryLockAction(CTORATstpSPQryLockActionField *pQryLockActionField, int nRequestID) = 0;
		
		//��ѯ��ĳֲ�ת����ϸ
		virtual int ReqQryStockPositionTransferDetail(CTORATstpSPQryStockPositionTransferDetailField *pQryStockPositionTransferDetailField, int nRequestID) = 0;
		
		//��ѯ����֪ͨ
		virtual int ReqQryTradingNotice(CTORATstpSPQryTradingNoticeField *pQryTradingNoticeField, int nRequestID) = 0;
		
		//��ѯ֤ȯ����
		virtual int ReqQryStockDisposal(CTORATstpSPQryStockDisposalField *pQryStockDisposalField, int nRequestID) = 0;
		
		//��ѯ֤ȯ���ó���
		virtual int ReqQryStockDisposalAction(CTORATstpSPQryStockDisposalActionField *pQryStockDisposalActionField, int nRequestID) = 0;
		
		//��ѯ������
		virtual int ReqQryCondOrder(CTORATstpSPQryCondOrderField *pQryCondOrderField, int nRequestID) = 0;
		
		//��ѯ����������
		virtual int ReqQryCondOrderAction(CTORATstpSPQryCondOrderActionField *pQryCondOrderActionField, int nRequestID) = 0;
		
		//��ѯͶ�����޲�
		virtual int ReqQryInvestorLimitPosition(CTORATstpSPQryInvestorLimitPositionField *pQryInvestorLimitPositionField, int nRequestID) = 0;
		
		//��ѯͶ�����޶�
		virtual int ReqQryInvestorLimitAmount(CTORATstpSPQryInvestorLimitAmountField *pQryInvestorLimitAmountField, int nRequestID) = 0;
		
		//��ѯ��ϳ���
		virtual int ReqQryCombOrderAction(CTORATstpSPQryCombOrderActionField *pQryCombOrderActionField, int nRequestID) = 0;
		
		//��ѯ��ϱ���
		virtual int ReqQryCombOrder(CTORATstpSPQryCombOrderField *pQryCombOrderField, int nRequestID) = 0;
		
		//��ѯ��ϳֲ�
		virtual int ReqQryCombPosition(CTORATstpSPQryCombPositionField *pQryCombPositionField, int nRequestID) = 0;
		
		//��ѯ��ϳֲ���ϸ
		virtual int ReqQryCombPosDetail(CTORATstpSPQryCombPosDetailField *pQryCombPosDetailField, int nRequestID) = 0;
		
		//��ѯͶ������Ȩָ����ϸ
		virtual int ReqQryExerciseAppointment(CTORATstpSPQryExerciseAppointmentField *pQryExerciseAppointmentField, int nRequestID) = 0;
		
		//��ѯ���ҹɷݲ����λ
		virtual int ReqQryInsufficientCoveredStockPosition(CTORATstpSPQryInsufficientCoveredStockPositionField *pQryInsufficientCoveredStockPositionField, int nRequestID) = 0;
		
		//��ѯ��Ϻ�Լ��Ϣ
		virtual int ReqQryCombSecurity(CTORATstpSPQryCombSecurityField *pQryCombSecurityField, int nRequestID) = 0;
		
		//��ѯ�ϲ���Ȩί��
		virtual int ReqQryCombExercise(CTORATstpSPQryCombExerciseField *pQryCombExerciseField, int nRequestID) = 0;
		
		//��ѯ�ϲ���Ȩ����
		virtual int ReqQryCombExerciseAction(CTORATstpSPQryCombExerciseActionField *pQryCombExerciseActionField, int nRequestID) = 0;
		
		
	protected:
		~CTORATstpSPTraderApi(){};
	};
}
#endif // _TORA_TSTPSPTRADERAPI_H