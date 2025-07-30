/////////////////////////////////////////////////////////////////////////
///@company �Ϻ�̩����Ϣ�Ƽ����޹�˾
///@file TORATstpSPUserApiDataType.h
///@brief �����˿ͻ��˽ӿ�ʹ�õ�ҵ����������
///@history 
/////////////////////////////////////////////////////////////////////////

#ifndef _TORA_TSTPSPUSERAPIDATATYPE_H
#define _TORA_TSTPSPUSERAPIDATATYPE_H

#include <limits.h>
#include <float.h>

namespace TORASPAPI
{
	///�����ֵ
	const int INT_NULL_VAL = INT_MAX;
	
	const double FLOAT_NULL_VAL = DBL_MAX;
	
	const char CHAR_NULL_VAL = 0;
	
	const short WORD_NULL_VAL = SHRT_MAX;
	
#ifdef WINDOWS
	const __int64 LONG_NULL_VAL = _I64_MAX;
#else
	const long long LONG_NULL_VAL = LLONG_MAX;
#endif
	
	///���������ÿպ��п�
	inline void set_null(int &v)
	{
		v = INT_NULL_VAL;
	}
	inline bool is_null(const int &v)
	{
		return v == INT_NULL_VAL;
	}
	
	///�����������ÿպ��п�
	inline void set_null(double &v)
	{
		v = FLOAT_NULL_VAL;
	}
	inline bool is_null(const double &v)
	{
		return v == FLOAT_NULL_VAL;
	}
	
	///�ַ��������ÿպ��п�
	inline void set_null(char &v)
	{
		v = CHAR_NULL_VAL;
	}
	inline bool is_null(const char &v)
	{
		return v == CHAR_NULL_VAL;
	}
	
	///�����������ÿպ��п�
	inline void set_null(short &v)
	{
		v = WORD_NULL_VAL;
	}
	inline bool is_null(const short &v)
	{
		return v == WORD_NULL_VAL;
	}
	
	///�����������ÿպ��п�
	#ifdef WINDOWS
	inline void set_null(__int64 &v)
	#else
	inline void set_null(long long &v)
	#endif
	{
		v = LONG_NULL_VAL;
	}
	#ifdef WINDOWS
	inline bool is_null(const __int64 &v)
	#else
	inline bool is_null(const long long &v)
	#endif
	{
		return v == LONG_NULL_VAL;
	}
	
	///�ַ����������ÿպ��п�
	inline void set_null(char *v)
	{
		v[0] = '\0';
	}
	inline bool is_null(const char *v)
	{
		const char *p=v;
		while (*p)
		{
			if (*p!=' ')
			{
				return false;
			}
			p++;
		}
		return true;
	}

	enum TORA_TE_RESUME_TYPE
	{
		TORA_TERT_RESTART = 0,
		TORA_TERT_RESUME,
		TORA_TERT_QUICK
	};


	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDateType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPDateType[9];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTimeType��һ��ʱ������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPTimeType[9];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMillisecType��һ��ʱ�䣨���룩����
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPMillisecType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPriceType��һ���۸�����
	/////////////////////////////////////////////////////////////////////////
	typedef double TTORATstpSPPriceType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRatioType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef double TTORATstpSPRatioType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMoneyType��һ���ʽ�����
	/////////////////////////////////////////////////////////////////////////
	typedef double TTORATstpSPMoneyType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpVolumeType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPVolumeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLargeVolumeType��һ�������������
	/////////////////////////////////////////////////////////////////////////
	typedef double TTORATstpSPLargeVolumeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBoolType��һ������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPBoolType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSequenceNoType��һ����ˮ������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPSequenceNoType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSerialType��һ����ˮ������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPSerialType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCommFluxType��һ��ͨѶ��������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPCommFluxType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExchangeIDType��һ����������������
	/////////////////////////////////////////////////////////////////////////
	///ͨ��(�ڲ�ʹ��)
	const char TORA_TSTP_SP_EXD_COMM = '0';
	///�Ϻ�������
	const char TORA_TSTP_SP_EXD_SSE = '1';
	///���ڽ�����
	const char TORA_TSTP_SP_EXD_SZSE = '2';
	///��۽�����
	const char TORA_TSTP_SP_EXD_HK = '3';
	typedef char TTORATstpSPExchangeIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpVolumeMultipleType��һ����Լ������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPVolumeMultipleType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpIdCardNoType��һ��֤���������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPIdCardNoType[51];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpUserIDType��һ�������û���������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPUserIDType[16];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTradeIDType��һ���ɽ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPTradeIDType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderSysIDType��һ��ϵͳ�����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPOrderSysIDType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExchangeCombIDType��һ����������ϱ�������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPExchangeCombIDType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPasswordType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPPasswordType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpFrontIDType��һ��ǰ�ñ������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPFrontIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSessionIDType��һ���Ự�������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPSessionIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpProductInfoType��һ����Ʒ��Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPProductInfoType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpProtocolInfoType��һ��Э����Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPProtocolInfoType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDataSyncStatusType��һ������ͬ��״̬����
	/////////////////////////////////////////////////////////////////////////
	///δͬ��
	const char TORA_TSTP_SP_DS_Asynchronous = '1';
	///ͬ����
	const char TORA_TSTP_SP_DS_Synchronizing = '2';
	///��ͬ��
	const char TORA_TSTP_SP_DS_Synchronized = '3';
	///ȫ��ͬ�����
	const char TORA_TSTP_SP_DS_AllSynchronized = '4';
	///Ԥͬ�����
	const char TORA_TSTP_SP_DS_PreSync = '5';
	typedef char TTORATstpSPDataSyncStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRecordCntType��һ����¼��������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPRecordCntType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpErrorIDType��һ�������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPErrorIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpErrorMsgType��һ��������Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPErrorMsgType[81];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPositionTypeType��һ���ֲ���������
	/////////////////////////////////////////////////////////////////////////
	///���ֲ�
	const char TORA_TSTP_SP_PT_Net = '1';
	///�ۺϳֲ�
	const char TORA_TSTP_SP_PT_Gross = '2';
	typedef char TTORATstpSPPositionTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCombinationStatusType��һ����ϳֲ�״̬����
	/////////////////////////////////////////////////////////////////////////
	///���
	const char TORA_TSTP_SP_CTS_Combined = '1';
	///������
	const char TORA_TSTP_SP_CTS_Splitted = '3';
	typedef char TTORATstpSPCombinationStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpNameType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPNameType[61];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSecurityIDType��һ����Լ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPSecurityIDType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExchSecurityIDType��һ����������Լ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPExchSecurityIDType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPriceTickType��һ����С�䶯��λ����
	/////////////////////////////////////////////////////////////////////////
	typedef double TTORATstpSPPriceTickType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTradingUnitType��һ�����׵�λ����
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPTradingUnitType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSecurityStatusType��һ��֤ȯ״̬����
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPSecurityStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpAccountIDType��һ��Ͷ�����ʽ��ʺ�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPAccountIDType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBankAccountIDType��һ��ǩԼ�����˺�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPBankAccountIDType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpInvestorIDType��һ��Ͷ���ߴ�������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPInvestorIDType[13];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpContacterType��һ����ϵ������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPContacterType[61];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpFaxType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPFaxType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpEmailType��һ��Email����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPEmailType[61];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpAddressType��һ��ͨѶ��ַ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPAddressType[101];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpZipCodeType��һ��������������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPZipCodeType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDepartmentIDType��һ�����Ŵ�������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPDepartmentIDType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBranchIDType��һ��Ӫҵ������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPBranchIDType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpContractNoType��һ����ͬ�������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPContractNoType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRemarkType��һ����ע����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPRemarkType[513];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTerminalInfoType��һ���ն���Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPTerminalInfoType[256];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpShareholderIDType��һ���ɶ��˻���������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPShareholderIDType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPbuIDType��һ�����׵�Ԫ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPPbuIDType[11];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpIPAddressType��һ��IP��ַ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPIPAddressType[16];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMacAddressType��һ��Mac��ַ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPMacAddressType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPortType��һ���˿ں�����
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPPortType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLangType��һ����������
	/////////////////////////////////////////////////////////////////////////
	///��������
	const char TORA_TSTP_SP_LGT_ZHCN = '0';
	///�������
	const char TORA_TSTP_SP_LGT_ZHHK = '1';
	///Ӣ������
	const char TORA_TSTP_SP_LGT_ENUS = '2';
	typedef char TTORATstpSPLangType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderLocalIDType��һ�����ر����������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPOrderLocalIDType[13];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBusinessUnitIDType��һ��Ͷ�ʵ�Ԫ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPBusinessUnitIDType[17];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSecurityNameType��һ��֤ȯ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPSecurityNameType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderRefType��һ��������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPOrderRefType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRequestIDType��һ������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPRequestIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpIntSerialType��һ��������ˮ������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPIntSerialType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpInvestorNameType��һ��Ͷ������������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPInvestorNameType[81];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpUserNameType��һ���û���������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPUserNameType[81];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLoginLimitType��һ����¼��������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPLoginLimitType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBankIDType��һ�����д�������
	/////////////////////////////////////////////////////////////////////////
	///�й���������
	const char TORA_TSTP_SP_BKID_CCB = '1';
	///�й�ũҵ����
	const char TORA_TSTP_SP_BKID_ABC = '2';
	///�й���������
	const char TORA_TSTP_SP_BKID_ICBC = '3';
	///�й�����
	const char TORA_TSTP_SP_BKID_BOC = '4';
	///�й���������
	const char TORA_TSTP_SP_BKID_CMBC = '5';
	///�й���ͨ����
	const char TORA_TSTP_SP_BKID_BC = '6';
	///�ֶ���չ����
	const char TORA_TSTP_SP_BKID_SPDB = '7';
	///��ҵ����
	const char TORA_TSTP_SP_BKID_CIB = '8';
	///�й��������
	const char TORA_TSTP_SP_BKID_CEB = '9';
	///�㶫��չ����
	const char TORA_TSTP_SP_BKID_GDB = 'a';
	///��������
	const char TORA_TSTP_SP_BKID_CITIC = 'b';
	///ƽ������
	const char TORA_TSTP_SP_BKID_SPABANK = 'c';
	typedef char TTORATstpSPBankIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCurrencyIDType��һ����������
	/////////////////////////////////////////////////////////////////////////
	///�����
	const char TORA_TSTP_SP_CID_CNY = '1';
	///�۱�
	const char TORA_TSTP_SP_CID_HKD = '2';
	///��Ԫ
	const char TORA_TSTP_SP_CID_USD = '3';
	typedef char TTORATstpSPCurrencyIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpActiveStatusType��һ���û�״̬����
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_USTS_Enabled = '1';
	///����
	const char TORA_TSTP_SP_USTS_Disabled = '2';
	///����
	const char TORA_TSTP_SP_USTS_Locked = '3';
	typedef char TTORATstpSPActiveStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpAuthModeType��һ����֤��ʽ����
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_AM_Password = '0';
	///ָ��
	const char TORA_TSTP_SP_AM_FingerPrint = '1';
	///Կ�״�
	const char TORA_TSTP_SP_AM_CertInfo = '2';
	typedef char TTORATstpSPAuthModeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDeviceTypeType��һ���豸�������
	/////////////////////////////////////////////////////////////////////////
	///PC��
	const char TORA_TSTP_SP_DT_PC = '0';
	///�ƶ���
	const char TORA_TSTP_SP_DT_Mobile = '1';
	typedef char TTORATstpSPDeviceTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDeviceIDType��һ���豸��ʶ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPDeviceIDType[129];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCertSerialType��һ����֤��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPCertSerialType[129];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCombOffsetFlagType��һ����Ͽ�ƽ��־����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPCombOffsetFlagType[5];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCombHedgeFlagType��һ�����Ͷ���ױ���־����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPCombHedgeFlagType[5];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTelephoneType��һ����ϵ�绰����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPTelephoneType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMobileType��һ���ֻ�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPMobileType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLongVolumeType��һ��LongVolume����
	/////////////////////////////////////////////////////////////////////////
	typedef long long int TTORATstpSPLongVolumeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderUnitType��һ���걨��λ����
	/////////////////////////////////////////////////////////////////////////
	///��
	const char TORA_TSTP_SP_OUT_Shou = '0';
	///��
	const char TORA_TSTP_SP_OUT_Gu = '1';
	///��
	const char TORA_TSTP_SP_OUT_Fen = '2';
	///��
	const char TORA_TSTP_SP_OUT_Zhang = '3';
	typedef char TTORATstpSPOrderUnitType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpInvestorTypeType��һ��Ͷ������������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_CT_Person = '0';
	///����
	const char TORA_TSTP_SP_CT_Company = '1';
	///��Ӫ
	const char TORA_TSTP_SP_CT_SelfOperate = '5';
	typedef char TTORATstpSPInvestorTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpIdCardTypeType��һ��֤����������
	/////////////////////////////////////////////////////////////////////////
	///��֯��������
	const char TORA_TSTP_SP_ICT_EID = '0';
	///�й��������֤
	const char TORA_TSTP_SP_ICT_IDCard = '1';
	///����֤
	const char TORA_TSTP_SP_ICT_OfficerIDCard = '2';
	///����֤
	const char TORA_TSTP_SP_ICT_PoliceIDCard = '3';
	///ʿ��֤
	const char TORA_TSTP_SP_ICT_SoldierIDCard = '4';
	///���ڲ�
	const char TORA_TSTP_SP_ICT_HouseholdRegister = '5';
	///����
	const char TORA_TSTP_SP_ICT_Passport = '6';
	///̨��֤
	const char TORA_TSTP_SP_ICT_TaiwanCompatriotIDCard = '7';
	///����֤
	const char TORA_TSTP_SP_ICT_HomeComingCard = '8';
	///Ӫҵִ�պ�
	const char TORA_TSTP_SP_ICT_LicenseNo = '9';
	///˰��ǼǺ�/������˰ID
	const char TORA_TSTP_SP_ICT_TaxNo = 'A';
	///�۰ľ��������ڵ�ͨ��֤
	const char TORA_TSTP_SP_ICT_HMMainlandTravelPermit = 'B';
	///̨�����������½ͨ��֤
	const char TORA_TSTP_SP_ICT_TwMainlandTravelPermit = 'C';
	///����
	const char TORA_TSTP_SP_ICT_DrivingLicense = 'D';
	///�����籣ID
	const char TORA_TSTP_SP_ICT_SocialID = 'F';
	///�������֤
	const char TORA_TSTP_SP_ICT_LocalID = 'G';
	///��ҵ�Ǽ�֤
	const char TORA_TSTP_SP_ICT_BusinessRegistration = 'H';
	///�۰������Ծ������֤
	const char TORA_TSTP_SP_ICT_HKMCIDCard = 'I';
	///���п������֤
	const char TORA_TSTP_SP_ICT_AccountsPermits = 'J';
	///����֤��
	const char TORA_TSTP_SP_ICT_OtherCard = 'x';
	typedef char TTORATstpSPIdCardTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpAccountTypeType��һ���ʽ��˻���������
	/////////////////////////////////////////////////////////////////////////
	///��ͨ
	const char TORA_TSTP_SP_FAT_Normal = '1';
	///����
	const char TORA_TSTP_SP_FAT_Credit = '2';
	///����Ʒ
	const char TORA_TSTP_SP_FAT_Derivatives = '3';
	typedef char TTORATstpSPAccountTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpDirectionType��һ��������������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_D_Buy = '0';
	///����
	const char TORA_TSTP_SP_D_Sell = '1';
	///�գ�������)
	const char TORA_TSTP_SP_D_Non = '*';
	typedef char TTORATstpSPDirectionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCombDirectionType��һ����ϱ�����������
	/////////////////////////////////////////////////////////////////////////
	///���
	const char TORA_TSTP_SP_CBD_Combine = '0';
	///���
	const char TORA_TSTP_SP_CBD_Split = '1';
	///ǿ��
	const char TORA_TSTP_SP_CBD_ForceSplit = '2';
	typedef char TTORATstpSPCombDirectionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBrokerageTypeType��һ��Ӷ����������
	/////////////////////////////////////////////////////////////////////////
	///ëӶ��
	const char TORA_TSTP_SP_BT_Gross = '0';
	///��Ӷ��
	const char TORA_TSTP_SP_BT_Net = '1';
	typedef char TTORATstpSPBrokerageTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpUserTypeType��һ���û���������
	/////////////////////////////////////////////////////////////////////////
	///���͹�˾�û�
	const char TORA_TSTP_SP_UTYPE_BrokerUser = '0';
	///�����û�
	const char TORA_TSTP_SP_UTYPE_SuperUser = '1';
	///Ͷ�����û�
	const char TORA_TSTP_SP_UTYPE_Investor = '2';
	typedef char TTORATstpSPUserTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOperateSourceType��һ��������Դ����
	/////////////////////////////////////////////////////////////////////////
	///ʵʱ�ϳ�
	const char TORA_TSTP_SP_OPRTSRC_DBCommand = '0';
	///API����
	const char TORA_TSTP_SP_OPRTSRC_SyncAPI = '1';
	///ʵʱģʽ�Զ�����
	const char TORA_TSTP_SP_OPRTSRC_RealTimeAuto = '2';
	typedef char TTORATstpSPOperateSourceType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOperwayType��һ��ί�з�ʽ��ö��ֵ���������ο��������ȯ��Ҫ����д������ַ�������
	/////////////////////////////////////////////////////////////////////////
	///�绰ί��
	const char TORA_TSTP_SP_OPERW_Telephone = '0';
	///��̨ί��
	const char TORA_TSTP_SP_OPERW_OTC = '1';
	///�ƶ��ͻ���ί��
	const char TORA_TSTP_SP_OPERW_MobileClient = '2';
	///PC�ͻ���ί��
	const char TORA_TSTP_SP_OPERW_PCClient = '3';
	///TYί��
	const char TORA_TSTP_SP_OPERW_TY = '4';
	typedef char TTORATstpSPOperwayType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOperwaysType��һ��ί�з�ʽ�ϼ�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPOperwaysType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderPriceTypeType��һ�������۸���������
	/////////////////////////////////////////////////////////////////////////
	///�����
	const char TORA_TSTP_SP_OPT_AnyPrice = '1';
	///�޼�
	const char TORA_TSTP_SP_OPT_LimitPrice = '2';
	///���ż�
	const char TORA_TSTP_SP_OPT_BestPrice = '3';
	///���¼�
	const char TORA_TSTP_SP_OPT_LastPrice = '4';
	///��ؼ�
	const char TORA_TSTP_SP_OPT_Relative = '5';
	///��һ��
	const char TORA_TSTP_SP_OPT_AskPrice1 = '8';
	///��һ��
	const char TORA_TSTP_SP_OPT_BidPrice1 = 'C';
	///�嵵��
	const char TORA_TSTP_SP_OPT_FiveLevelPrice = 'G';
	///��������
	const char TORA_TSTP_SP_OPT_HomeBestPrice = 'a';
	typedef char TTORATstpSPOrderPriceTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTimeConditionType��һ����Ч����������
	/////////////////////////////////////////////////////////////////////////
	///������ɣ�������
	const char TORA_TSTP_SP_TC_IOC = '1';
	///������Ч
	const char TORA_TSTP_SP_TC_GFS = '2';
	///������Ч
	const char TORA_TSTP_SP_TC_GFD = '3';
	///ָ������ǰ��Ч
	const char TORA_TSTP_SP_TC_GTD = '4';
	///����ǰ��Ч
	const char TORA_TSTP_SP_TC_GTC = '5';
	///���Ͼ�����Ч
	const char TORA_TSTP_SP_TC_GFA = '6';
	typedef char TTORATstpSPTimeConditionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpVolumeConditionType��һ���ɽ�����������
	/////////////////////////////////////////////////////////////////////////
	///�κ�����
	const char TORA_TSTP_SP_VC_AV = '1';
	///��С����
	const char TORA_TSTP_SP_VC_MV = '2';
	///ȫ������
	const char TORA_TSTP_SP_VC_CV = '3';
	typedef char TTORATstpSPVolumeConditionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpForceCloseReasonType��һ��ǿƽԭ������
	/////////////////////////////////////////////////////////////////////////
	///��ǿƽ
	const char TORA_TSTP_SP_FCC_NotForceClose = '0';
	///�ʽ���
	const char TORA_TSTP_SP_FCC_LackDeposit = '1';
	///�ͻ�����
	const char TORA_TSTP_SP_FCC_ClientOverPositionLimit = '2';
	///��Ա����
	const char TORA_TSTP_SP_FCC_MemberOverPositionLimit = '3';
	///�ֲַ�������
	const char TORA_TSTP_SP_FCC_NotMultiple = '4';
	///Υ��
	const char TORA_TSTP_SP_FCC_Violation = '5';
	///����
	const char TORA_TSTP_SP_FCC_Other = '6';
	typedef char TTORATstpSPForceCloseReasonType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCancelOrderStatusType��һ������״̬����
	/////////////////////////////////////////////////////////////////////////
	///�������ύ
	const char TORA_TSTP_SP_CORDS_Submitted = 'a';
	///�����ѳɹ�
	const char TORA_TSTP_SP_CORDS_Canceled = 'b';
	///����ʧ��
	const char TORA_TSTP_SP_CORDS_Fail = 'c';
	typedef char TTORATstpSPCancelOrderStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTransferDirectionType��һ��ת�Ʒ�������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_TRNSD_In = '0';
	///���
	const char TORA_TSTP_SP_TRNSD_Out = '1';
	///����
	const char TORA_TSTP_SP_TRNSD_MoveIn = '2';
	///����
	const char TORA_TSTP_SP_TRNSD_MoveOut = '3';
	///����
	const char TORA_TSTP_SP_TRNSD_Freeze = '4';
	///�ⶳ
	const char TORA_TSTP_SP_TRNSD_UnFreeze = '5';
	///��֤ת��
	const char TORA_TSTP_SP_TRNSD_TransferIn = '6';
	///��֤ת��
	const char TORA_TSTP_SP_TRNSD_TransferOut = '7';
	typedef char TTORATstpSPTransferDirectionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSPStockTransferReasonType��һ��������Ȩ����ֻ�ת��ԭ������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_SSTR_In = '0';
	///���
	const char TORA_TSTP_SP_SSTR_Out = '1';
	///����
	const char TORA_TSTP_SP_SSTR_MoveIn = 'a';
	///����
	const char TORA_TSTP_SP_SSTR_MoveOut = 'b';
	///������������
	const char TORA_TSTP_SP_SSTR_Lock = 'c';
	///���������������
	const char TORA_TSTP_SP_SSTR_LockRepeal = 'k';
	///�������������ⶳ
	const char TORA_TSTP_SP_SSTR_LockCancel = 'q';
	///���ҽ����ⶳ
	const char TORA_TSTP_SP_SSTR_UnLock = 'd';
	///��Ȩ����
	const char TORA_TSTP_SP_SSTR_Exercise = 'e';
	///��Ȩ�������
	const char TORA_TSTP_SP_SSTR_ExerciseRepeal = 'l';
	///��Ȩ�����ⶳ
	const char TORA_TSTP_SP_SSTR_ExerciseCancel = 'f';
	///��֤��ת���Ҷ���
	const char TORA_TSTP_SP_SSTR_MarginToCover = 'h';
	///��֤��ת���Ҷ���ⶳ
	const char TORA_TSTP_SP_SSTR_MarginToCoverRepeal = 'i';
	///��֤��ת���ҳ����ⶳ
	const char TORA_TSTP_SP_SSTR_MarginToCoverCancel = 'p';
	///����ת��֤��
	const char TORA_TSTP_SP_SSTR_CoverToMargin = 'j';
	///���ҿ��ֶ���
	const char TORA_TSTP_SP_SSTR_CoverOpen = 'm';
	///���ҿ��ֶ������
	const char TORA_TSTP_SP_SSTR_CoverOpenRepeal = 'n';
	///���ҿ��ֳ����ⶳ
	const char TORA_TSTP_SP_SSTR_CoverOpenCancel = 'o';
	///����ƽ�ֽⶳ
	const char TORA_TSTP_SP_SSTR_CoverClose = 'g';
	typedef char TTORATstpSPSPStockTransferReasonType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTransferStatusType��һ��ת��״̬����
	/////////////////////////////////////////////////////////////////////////
	///Transfer���ڴ���
	const char TORA_TSTP_SP_TRANST_TransferHandling = '0';
	///Transfer�ɹ�
	const char TORA_TSTP_SP_TRANST_TransferSuccess = '1';
	///Transferʧ��
	const char TORA_TSTP_SP_TRANST_TransferFail = '2';
	///Repeal���ڴ���
	const char TORA_TSTP_SP_TRANST_RepealHandling = '3';
	///Repeal�ɹ�
	const char TORA_TSTP_SP_TRANST_RepealSuccess = '4';
	///Repealʧ��
	const char TORA_TSTP_SP_TRANST_RepealFail = '5';
	///�ⲿϵͳ�ѽ���
	const char TORA_TSTP_SP_TRANST_ExternalAccepted = '6';
	typedef char TTORATstpSPTransferStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpTransferPositionTypeType��һ��ת�Ƴֲ���������
	/////////////////////////////////////////////////////////////////////////
	///�����
	const char TORA_TSTP_SP_TPT_ALL = '0';
	///���
	const char TORA_TSTP_SP_TPT_History = '1';
	///��������
	const char TORA_TSTP_SP_TPT_TodayBS = '2';
	///�������
	const char TORA_TSTP_SP_TPT_TodayPR = '3';
	typedef char TTORATstpSPTransferPositionTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBizRefType��һ��ҵ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPBizRefType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSystemNameType��һ��ϵͳ��������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPSystemNameType[41];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderStatusType��һ������״̬����
	/////////////////////////////////////////////////////////////////////////
	///�����Ѵ���
	const char TORA_TSTP_SP_OST_Handled = '0';
	///�������ѽ���
	const char TORA_TSTP_SP_OST_Accepted = '1';
	///���ֳɽ�
	const char TORA_TSTP_SP_OST_PartTraded = '2';
	///ȫ���ɽ�
	const char TORA_TSTP_SP_OST_AllTraded = '3';
	///����
	const char TORA_TSTP_SP_OST_PartTradedCancelled = '4';
	///ȫ��
	const char TORA_TSTP_SP_OST_Cancelled = '5';
	///�ϵ�
	const char TORA_TSTP_SP_OST_Failed = '6';
	///Ԥ��
	const char TORA_TSTP_SP_OST_Cached = '7';
	///�����ֻ�ϵͳ����
	const char TORA_TSTP_SP_OST_SendStock = '8';
	///�������׺��Ĵ���
	const char TORA_TSTP_SP_OST_SendTradeKernel = '9';
	///��
	const char TORA_TSTP_SP_OST_NON = 'a';
	typedef char TTORATstpSPOrderStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderOperateStatusType��һ����������״̬����
	/////////////////////////////////////////////////////////////////////////
	///�Ѿ��ύ
	const char TORA_TSTP_SP_OOS_InsertSubmitted = '0';
	///�����Ѿ��ύ
	const char TORA_TSTP_SP_OOS_CancelSubmitted = '1';
	///�Ѿ�����
	const char TORA_TSTP_SP_OOS_Accepted = '2';
	///�����Ѿ����ܾ�
	const char TORA_TSTP_SP_OOS_InsertRejected = '3';
	///�����Ѿ����ܾ�
	const char TORA_TSTP_SP_OOS_CancelRejected = '4';
	///δ�ύ
	const char TORA_TSTP_SP_OOS_UnSubmitted = '5';
	typedef char TTORATstpSPOrderOperateStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOffsetFlagType��һ����ƽ��־����
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_OF_Open = '0';
	///ƽ��
	const char TORA_TSTP_SP_OF_Close = '1';
	///ǿƽ
	const char TORA_TSTP_SP_OF_ForceClose = '2';
	///ƽ��
	const char TORA_TSTP_SP_OF_CloseToday = '3';
	///ƽ��
	const char TORA_TSTP_SP_OF_CloseYesterday = '4';
	///ǿ��
	const char TORA_TSTP_SP_OF_ForceOff = '5';
	///����ǿƽ
	const char TORA_TSTP_SP_OF_LocalForceClose = '6';
	///��Ȩ���ڲ�ʹ�ã�
	const char TORA_TSTP_SP_OF_Exercise = '7';
	///�������ڲ�ʹ�ã�
	const char TORA_TSTP_SP_OF_Lock = '8';
	///�������ڲ�ʹ�ã�
	const char TORA_TSTP_SP_OF_UnLock = '9';
	///��ϣ��ڲ�ʹ�ã�
	const char TORA_TSTP_SP_OF_Combine = 'a';
	///��֣��ڲ�ʹ�ã�
	const char TORA_TSTP_SP_OF_Split = 'b';
	///����ƽ��
	const char TORA_TSTP_SP_OF_UnilateralClose = 'e';
	typedef char TTORATstpSPOffsetFlagType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCountType��һ����������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPCountType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpHedgeFlagType��һ��Ͷ���ױ���־����
	/////////////////////////////////////////////////////////////////////////
	///Ͷ��
	const char TORA_TSTP_SP_HF_Speculation = '1';
	///����
	const char TORA_TSTP_SP_HF_Arbitrage = '2';
	///�ױ�
	const char TORA_TSTP_SP_HF_Hedge = '3';
	///����
	const char TORA_TSTP_SP_HF_Covered = '4';
	///���б���(�ڲ�ʹ��)
	const char TORA_TSTP_SP_HF_MarketMaker = '5';
	typedef char TTORATstpSPHedgeFlagType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderActionFlagType��һ��ί�в�����־����
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_OAF_Delete = '0';
	///ǿ�Ƴ���
	const char TORA_TSTP_SP_OAF_ForceDelete = '1';
	typedef char TTORATstpSPOrderActionFlagType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExerciseDirectionType��һ����Ȩ��������
	/////////////////////////////////////////////////////////////////////////
	///������Ȩ
	const char TORA_TSTP_SP_EXCD_Active = '0';
	///������Ȩ
	const char TORA_TSTP_SP_EXCD_Passive = '1';
	typedef char TTORATstpSPExerciseDirectionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCoverFlagType��һ�����ұ�־����
	/////////////////////////////////////////////////////////////////////////
	///�Ǳ���
	const char TORA_TSTP_SP_CVF_Uncovered = '0';
	///����
	const char TORA_TSTP_SP_CVF_Covered = '1';
	typedef char TTORATstpSPCoverFlagType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMDSubModeType��һ�����鶩��ģʽ����
	/////////////////////////////////////////////////////////////////////////
	///TCP����ģʽ
	const char TORA_TSTP_SP_MST_TCP = '0';
	///UDP����ģʽ
	const char TORA_TSTP_SP_MST_UDP = '1';
	///UDP�鲥ģʽ
	const char TORA_TSTP_SP_MST_MCAST = '2';
	typedef char TTORATstpSPMDSubModeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpShareholderIDTypeType��һ���ɶ�������������
	/////////////////////////////////////////////////////////////////////////
	///δ֪
	const char TORA_TSTP_SP_SHID_Unknown = '0';
	///��ͨ
	const char TORA_TSTP_SP_SHID_Normal = '1';
	///����
	const char TORA_TSTP_SP_SHID_Credit = '2';
	///����Ʒ
	const char TORA_TSTP_SP_SHID_Derivatives = '3';
	typedef char TTORATstpSPShareholderIDTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpStrikeModeType��һ��ִ�з�ʽ����
	/////////////////////////////////////////////////////////////////////////
	///ŷʽ
	const char TORA_TSTP_SP_STM_Continental = '0';
	///��ʽ
	const char TORA_TSTP_SP_STM_American = '1';
	///��Ľ��
	const char TORA_TSTP_SP_STM_Bermuda = '2';
	typedef char TTORATstpSPStrikeModeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOptionsTypeType��һ����Ȩ��������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_CP_CallOptions = '1';
	///����
	const char TORA_TSTP_SP_CP_PutOptions = '2';
	typedef char TTORATstpSPOptionsTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpProductIDType��һ����ԼƷ�ִ�������
	/////////////////////////////////////////////////////////////////////////
	///ͨ��(�ڲ�ʹ��)
	const char TORA_TSTP_SP_PID_COMMON = '0';
	///�Ϻ���Ʊ
	const char TORA_TSTP_SP_PID_SHStock = '1';
	///�Ϻ�����
	const char TORA_TSTP_SP_PID_SHFund = '3';
	///�Ϻ�ծȯ
	const char TORA_TSTP_SP_PID_SHBond = '4';
	///���ڹ�Ʊ
	const char TORA_TSTP_SP_PID_SZStock = '7';
	///���ڻ���
	const char TORA_TSTP_SP_PID_SZFund = '9';
	///����ծȯ
	const char TORA_TSTP_SP_PID_SZBond = 'a';
	///�Ϻ�������Ȩ
	const char TORA_TSTP_SP_PID_SHStockOption = 'd';
	///���ڸ�����Ȩ
	const char TORA_TSTP_SP_PID_SZStockOption = 'e';
	typedef char TTORATstpSPProductIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSecurityTypeType��һ����Լ�������
	/////////////////////////////////////////////////////////////////////////
	///ͨ��(�ڲ�ʹ��)
	const char TORA_TSTP_SP_STP_COMMON = '0';
	///�Ϻ���Ʊ�Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SHCallAStockOption = '1';
	///�Ϻ���Ʊ�Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SHPullAStockOption = '2';
	///�Ϻ������Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SHCallFundStockOption = '3';
	///�Ϻ������Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SHPullFundStockOption = '4';
	///���ڹ�Ʊ�Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SZCallAStockOption = '5';
	///���ڹ�Ʊ�Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SZPullAStockOption = '6';
	///���ڻ����Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SZCallFundStockOption = '7';
	///���ڻ����Ϳ�����Ȩ
	const char TORA_TSTP_SP_STP_SZPullFundStockOption = '8';
	///�Ϻ������Ȩ
	const char TORA_TSTP_SP_STP_SHCombOption = '9';
	///���������Ȩ
	const char TORA_TSTP_SP_STP_SZCombOption = 'a';
	typedef char TTORATstpSPSecurityTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBusinessClassType��һ��ҵ���������
	/////////////////////////////////////////////////////////////////////////
	///���뿪��
	const char TORA_TSTP_SP_BC_BuyOpen = 'A';
	///����ƽ��
	const char TORA_TSTP_SP_BC_BuyClose = 'B';
	///��������
	const char TORA_TSTP_SP_BC_SellOpen = 'C';
	///����ƽ��
	const char TORA_TSTP_SP_BC_SellClose = 'D';
	///���ҿ���
	const char TORA_TSTP_SP_BC_CoveredOpen = 'E';
	///����ƽ��
	const char TORA_TSTP_SP_BC_CoveredClose = 'F';
	///��Ȩ
	const char TORA_TSTP_SP_BC_ExecOrder = 'G';
	///����ƽ�֣���ƽ����֣�
	const char TORA_TSTP_SP_BC_UnilateralBuyClose = 'H';
	///��Ч
	const char TORA_TSTP_SP_BC_Invalid = 'I';
	///�������뿪��
	const char TORA_TSTP_SP_BC_QuoteBuyOpen = 'J';
	///��������ƽ��
	const char TORA_TSTP_SP_BC_QuoteBuyClose = 'K';
	///������������
	const char TORA_TSTP_SP_BC_QuoteSellOpen = 'L';
	///��������ƽ��
	const char TORA_TSTP_SP_BC_QuoteSellClose = 'M';
	typedef char TTORATstpSPBusinessClassType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpSystemFlagType��һ��ϵͳ��ʶ����
	/////////////////////////////////////////////////////////////////////////
	///�ֻ�ϵͳ
	const char TORA_TSTP_SP_SFT_Stock = '0';
	///��Ȩϵͳ
	const char TORA_TSTP_SP_SFT_Option = '1';
	///����ϵͳ
	const char TORA_TSTP_SP_SFT_Credit = '2';
	///����ϵͳ
	const char TORA_TSTP_SP_SFT_MarketData = '3';
	///Lev2����ϵͳ
	const char TORA_TSTP_SP_SFT_Lev2MarketData = '4';
	typedef char TTORATstpSPSystemFlagType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpPosiDirectionType��һ���ֲֶ�շ�������
	/////////////////////////////////////////////////////////////////////////
	///��
	const char TORA_TSTP_SP_PD_Net = '1';
	///��ͷ
	const char TORA_TSTP_SP_PD_Long = '2';
	///��ͷ
	const char TORA_TSTP_SP_PD_Short = '3';
	typedef char TTORATstpSPPosiDirectionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMarketIDType��һ���г���������
	/////////////////////////////////////////////////////////////////////////
	///ͨ��(�ڲ�ʹ��)
	const char TORA_TSTP_SP_MKD_COMMON = '0';
	///�Ϻ�A��
	const char TORA_TSTP_SP_MKD_SHA = '1';
	///����A��
	const char TORA_TSTP_SP_MKD_SZA = '2';
	///�Ϻ�B��
	const char TORA_TSTP_SP_MKD_SHB = '3';
	///����B��
	const char TORA_TSTP_SP_MKD_SZB = '4';
	///��������A��
	const char TORA_TSTP_SP_MKD_SZThreeA = '5';
	///��������B��
	const char TORA_TSTP_SP_MKD_SZThreeB = '6';
	///�����г�
	const char TORA_TSTP_SP_MKD_Foreign = '7';
	typedef char TTORATstpSPMarketIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLogInAccountType��һ����¼�˻�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPLogInAccountType[21];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLogInAccountTypeType��һ����¼�˻���������
	/////////////////////////////////////////////////////////////////////////
	///�û�����
	const char TORA_TSTP_SP_LACT_UserID = '0';
	///�ʽ��˺�
	const char TORA_TSTP_SP_LACT_AccountID = '1';
	///�Ϻ�A��
	const char TORA_TSTP_SP_LACT_SHAStock = '2';
	///����A��
	const char TORA_TSTP_SP_LACT_SZAStock = '3';
	///�Ϻ�B��
	const char TORA_TSTP_SP_LACT_SHBStock = '4';
	///����B��
	const char TORA_TSTP_SP_LACT_SZBStock = '5';
	///����A
	const char TORA_TSTP_SP_LACT_ThreeNewBoardA = '6';
	///����B
	const char TORA_TSTP_SP_LACT_ThreeNewBoardB = '7';
	///�۹�
	const char TORA_TSTP_SP_LACT_HKStock = '8';
	///ͳһ�û�����
	const char TORA_TSTP_SP_LACT_UnifiedUserID = '9';
	typedef char TTORATstpSPLogInAccountTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMarketStatusType��һ���г�״̬����
	/////////////////////////////////////////////////////////////////////////
	///δ֪
	const char TORA_TSTP_SP_MST_UnKnown = '#';
	///����ǰ
	const char TORA_TSTP_SP_MST_BeforeTrading = '0';
	///��������
	const char TORA_TSTP_SP_MST_Continous = '1';
	///����
	const char TORA_TSTP_SP_MST_Closed = '2';
	///���̼��Ͼ���
	const char TORA_TSTP_SP_MST_OpenCallAuction = '3';
	typedef char TTORATstpSPMarketStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpBigsInfoType��һ�����ַ���������Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPBigsInfoType[33];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpShortsInfoType��һ�����ַ���������Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPShortsInfoType[9];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpIntInfoType��һ�����θ�����Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPIntInfoType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpApiGroupIDType��һ��Api�����������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPApiGroupIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpApiRunModeType��һ��Api����ģʽ����
	/////////////////////////////////////////////////////////////////////////
	///��һ
	const char TORA_TSTP_SP_ARM_Single = '0';
	///��Ⱥ
	const char TORA_TSTP_SP_ARM_Group = '1';
	typedef char TTORATstpSPApiRunModeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpInvestorLevelType��һ��Ͷ���߷ּ��������
	/////////////////////////////////////////////////////////////////////////
	///���ϸ�Ͷ����
	const char TORA_TSTP_SP_IVL_Invalid = '0';
	///һ��
	const char TORA_TSTP_SP_IVL_First = '1';
	///����
	const char TORA_TSTP_SP_IVL_Second = '2';
	///����
	const char TORA_TSTP_SP_IVL_Third = '3';
	typedef char TTORATstpSPInvestorLevelType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCondCheckType��һ��ί�������������
	/////////////////////////////////////////////////////////////////////////
	///�����κμ��
	const char TORA_TSTP_SP_CCT_None = '0';
	///�Գɽ����
	const char TORA_TSTP_SP_CCT_SelfDeal = '1';
	typedef char TTORATstpSPCondCheckType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpHDSerialType��һ��Ӳ�����к�����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPHDSerialType[33];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpStatusMsgType��һ��״̬��Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPStatusMsgType[121];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLockTypeType��һ�������������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_LT_Lock = '0';
	///����
	const char TORA_TSTP_SP_LT_UnLock = '1';
	typedef char TTORATstpSPLockTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpLockStatusType��һ�������걨״̬����
	/////////////////////////////////////////////////////////////////////////
	///�����ֻ�ϵͳ
	const char TORA_TSTP_SP_LST_SendStock = '0';
	///��������
	const char TORA_TSTP_SP_LST_SendOffer = '2';
	///����/����ʧ��
	const char TORA_TSTP_SP_LST_Fail = '3';
	///����/�����ɹ�
	const char TORA_TSTP_SP_LST_Success = '4';
	///ǿ�Ƴ���
	const char TORA_TSTP_SP_LST_ForceCancell = '5';
	typedef char TTORATstpSPLockStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExerciseTypeType��һ����Ȩִ����������
	/////////////////////////////////////////////////////////////////////////
	///ִ��
	const char TORA_TSTP_SP_EXERT_Execute = '1';
	///����
	const char TORA_TSTP_SP_EXERT_Drop = '2';
	typedef char TTORATstpSPExerciseTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpExerciseStatusType��һ����Ȩִ��״̬����
	/////////////////////////////////////////////////////////////////////////
	///�����ֻ�ϵͳ
	const char TORA_TSTP_SP_EXERS_SendStock = '0';
	///��������
	const char TORA_TSTP_SP_EXERS_SendOffer = '2';
	///��Ȩʧ��
	const char TORA_TSTP_SP_EXERS_Fail = '3';
	///�������ѽ���
	const char TORA_TSTP_SP_EXERS_Accepted = '4';
	///��Ȩ�ѳ���
	const char TORA_TSTP_SP_EXERS_Cancelled = '5';
	typedef char TTORATstpSPExerciseStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpStockDisposalTypeType��һ��֤ȯ�����������
	/////////////////////////////////////////////////////////////////////////
	///���뵽֤ȯ��˾�˻�
	const char TORA_TSTP_SP_SDT_Broker = '1';
	///���뵽Ͷ����֤ȯ�˻�
	const char TORA_TSTP_SP_SDT_Investor = '2';
	typedef char TTORATstpSPStockDisposalTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpStockDisposalStatusType��һ��֤ȯ����״̬����
	/////////////////////////////////////////////////////////////////////////
	///��������
	const char TORA_TSTP_SP_SDS_SendOffer = '1';
	///ʧ��
	const char TORA_TSTP_SP_SDS_Fail = '2';
	///�������ѽ���
	const char TORA_TSTP_SP_SDS_Accepted = '3';
	///֤ȯ�����ѳ���
	const char TORA_TSTP_SP_SDS_Cancelled = '4';
	typedef char TTORATstpSPStockDisposalStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCombinationStrategyType��һ����ϲ�������
	/////////////////////////////////////////////////////////////////////////
	///�Ϲ�ţ�м۲����
	const char TORA_TSTP_SP_CBS_CNSJC = '1';
	///�Ϲ����м۲����
	const char TORA_TSTP_SP_CBS_CXSJC = '2';
	///�Ϲ����м۲����
	const char TORA_TSTP_SP_CBS_PXSJC = '3';
	///�Ϲ�ţ�м۲����
	const char TORA_TSTP_SP_CBS_PNSJC = '4';
	///��ʽ��ͷ
	const char TORA_TSTP_SP_CBS_KS = '5';
	///���ʽ��ͷ
	const char TORA_TSTP_SP_CBS_KKS = '6';
	///��֤�𿪲�ת����
	const char TORA_TSTP_SP_CBS_ZBD = '7';
	///���Ҳ�ת��ͨ
	const char TORA_TSTP_SP_CBS_ZXJ = '8';
	typedef char TTORATstpSPCombinationStrategyType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMDSecurityStatType��һ������֤ȯ״̬����
	/////////////////////////////////////////////////////////////////////////
	///����ǰ
	const char TORA_TSTP_SP_MSST_PreOpen = '0';
	///���Ͼ���
	const char TORA_TSTP_SP_MSST_CallAuction = '1';
	///��������
	const char TORA_TSTP_SP_MSST_Continous = '2';
	///����
	const char TORA_TSTP_SP_MSST_Pause = '3';
	///ͣ��
	const char TORA_TSTP_SP_MSST_Suspend = '4';
	///����ͣ��
	const char TORA_TSTP_SP_MSST_LongSuspend = '5';
	///�������ж�
	const char TORA_TSTP_SP_MSST_UndulationInt = '6';
	///�۶Ͽɻָ�
	const char TORA_TSTP_SP_MSST_CircuitBreak = '7';
	///�۶ϲ��ɻָ�
	const char TORA_TSTP_SP_MSST_CircuitBreakU = '8';
	///����
	const char TORA_TSTP_SP_MSST_Close = '9';
	///����
	const char TORA_TSTP_SP_MSST_Other = 'a';
	///���̼��Ͼ���
	const char TORA_TSTP_SP_MSST_CloseCallAuction = 'b';
	typedef char TTORATstpSPMDSecurityStatType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCondOrderIDType��һ�����������������
	/////////////////////////////////////////////////////////////////////////
	typedef int TTORATstpSPCondOrderIDType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpContingentConditionType��һ��������������
	/////////////////////////////////////////////////////////////////////////
	///�ɽ�����
	const char TORA_TSTP_SP_CC_TradeTouch = '0';
	///��������
	const char TORA_TSTP_SP_CC_CancelTouch = '1';
	///ʱ�䴥��
	const char TORA_TSTP_SP_CC_TimeTouch = '2';
	///����ʱ�δ���
	const char TORA_TSTP_SP_CC_SegmentTouch = '3';
	///���¼۴��ڵ���������
	const char TORA_TSTP_SP_CC_LastPriceGreaterThanStopPrice = '4';
	///���¼�С�ڵ���������
	const char TORA_TSTP_SP_CC_LastPriceLesserThanStopPrice = '5';
	///��һ�۴��ڵ���������
	const char TORA_TSTP_SP_CC_AskPriceGreaterEqualStopPrice = '6';
	///��һ��С�ڵ���������
	const char TORA_TSTP_SP_CC_AskPriceLesserEqualStopPrice = '7';
	///��һ�۴��ڵ���������
	const char TORA_TSTP_SP_CC_BidPriceGreaterEqualStopPrice = '8';
	///��һ��С�ڵ���������
	const char TORA_TSTP_SP_CC_BidPriceLesserEqualStopPrice = '9';
	typedef char TTORATstpSPContingentConditionType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpOrderVolumeTypeType��һ������������������
	/////////////////////////////////////////////////////////////////////////
	///�Զ�������
	const char TORA_TSTP_SP_OVT_CustomVol = '1';
	///�������
	const char TORA_TSTP_SP_OVT_RelativeVol = '2';
	typedef char TTORATstpSPOrderVolumeTypeType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpCondOrderStatusType��һ��������״̬����
	/////////////////////////////////////////////////////////////////////////
	///��ʼ
	const char TORA_TSTP_SP_COST_Initial = '#';
	///δ����
	const char TORA_TSTP_SP_COST_NotTouched = '0';
	///�Ѵ���
	const char TORA_TSTP_SP_COST_Touched = '1';
	///�ѽ���
	const char TORA_TSTP_SP_COST_Finished = '2';
	///�ѳ���
	const char TORA_TSTP_SP_COST_Cancel = '3';
	///����ʧ��
	const char TORA_TSTP_SP_COST_Failed = '4';
	typedef char TTORATstpSPCondOrderStatusType;

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRelativeCondParamType��һ�����������������
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPRelativeCondParamType[31];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpMessageType��һ��֪ͨ��Ϣ����
	/////////////////////////////////////////////////////////////////////////
	typedef char TTORATstpSPMessageType[513];

	/////////////////////////////////////////////////////////////////////////
	/// TTORATstpRiskLevelType��һ�����ռ�������
	/////////////////////////////////////////////////////////////////////////
	///����
	const char TORA_TSTP_SP_RL_None = '0';
	///��ʾ
	const char TORA_TSTP_SP_RL_Warn = '1';
	///׷��
	const char TORA_TSTP_SP_RL_Call = '2';
	///ǿƽ
	const char TORA_TSTP_SP_RL_Force = '3';
	///����
	const char TORA_TSTP_SP_RL_Wear = '4';
	///�쳣
	const char TORA_TSTP_SP_RL_Exception = '5';
	typedef char TTORATstpSPRiskLevelType;
}
#endif