import uuid
from decimal import Decimal
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q

from .models import WaterPricePolicy, WaterUser, WaterBill, WaterPayment
from rest_framework import serializers
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response


def generate_code(prefix):
    date_str = timezone.now().strftime('%Y%m%d')
    return f'{prefix}{date_str}{str(uuid.uuid4())[:6].upper()}'


class WaterPricePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterPricePolicy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterUserSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)

    class Meta:
        model = WaterUser
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterBillSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    region_name = serializers.CharField(source='user.region.name', read_only=True)

    class Meta:
        model = WaterBill
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterPaymentSerializer(serializers.ModelSerializer):
    bill_code = serializers.CharField(source='bill.code', read_only=True)
    user_name = serializers.CharField(source='bill.user.name', read_only=True)

    class Meta:
        model = WaterPayment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterPricePolicyViewSet(viewsets.ModelViewSet):
    queryset = WaterPricePolicy.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['policy_type', 'pricing_mode', 'region', 'is_active']
    search_fields = ['code', 'name']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterPricePolicySerializer


class WaterUserViewSet(viewsets.ModelViewSet):
    queryset = WaterUser.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user_type', 'region', 'policy', 'is_active']
    search_fields = ['code', 'name', 'contact_person', 'water_meter']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterUserSerializer


class WaterBillViewSet(viewsets.ModelViewSet):
    queryset = WaterBill.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'policy', 'status', 'user__region']
    search_fields = ['code', 'user__name']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterBillSerializer

    def perform_create(self, serializer):
        instance = serializer.save(code=generate_code('BILL'))
        self._calculate_fees(instance)

    def _calculate_fees(self, bill):
        usage = bill.current_reading - bill.previous_reading
        bill.usage = usage

        if not bill.policy:
            bill.total_fee = Decimal('0.00')
            bill.save(update_fields=['usage', 'total_fee'])
            return

        policy = bill.policy
        base_fee = usage * policy.base_price

        tier_fee = Decimal('0.00')
        if policy.pricing_mode == '阶梯' and policy.tiers:
            remaining = usage
            for tier in policy.tiers:
                limit = tier.get('limit', 0)
                price = Decimal(str(tier.get('price', 0)))
                if remaining > 0 and limit > 0:
                    tier_fee += Decimal(str(min(remaining, limit))) * price
                    remaining -= limit
                elif remaining > 0:
                    tier_fee += Decimal(str(remaining)) * price
                    break

        tax_fee = (base_fee + tier_fee) * (Decimal(str(policy.tax_rate)) / Decimal('100'))

        total_fee = base_fee + tier_fee + tax_fee - bill.subsidy
        bill.base_fee = base_fee
        bill.tier_fee = tier_fee
        bill.tax_fee = tax_fee
        bill.total_fee = max(total_fee, Decimal('0.00'))
        bill.save(update_fields=['usage', 'base_fee', 'tier_fee', 'tax_fee', 'total_fee'])

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_bills(self, request):
        from django.db import transaction
        user_id = request.data.get('user_id')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')

        with transaction.atomic():
            users = WaterUser.objects.filter(id=user_id) if user_id else WaterUser.objects.filter(is_active=True)
            count = 0
            for user in users:
                last_bill = user.bills.order_by('-billing_period_end').first()
                previous_reading = last_bill.current_reading if last_bill else 0
                current_reading = previous_reading + request.data.get('default_usage', 0)

                bill = WaterBill.objects.create(
                    code=generate_code('BILL'),
                    user=user,
                    policy=user.policy,
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                    previous_reading=previous_reading,
                    current_reading=current_reading,
                    due_date=timezone.now().date().replace(day=28),
                    created_by=request.user,
                )
                self._calculate_fees(bill)
                count += 1

        return success_response(data={'count': count}, message=f'成功生成 {count} 条账单')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        total_fee = WaterBill.objects.aggregate(total=Sum('total_fee'))['total'] or 0
        paid_fee = WaterBill.objects.aggregate(total=Sum('paid_fee'))['total'] or 0

        return success_response(data={
            'total_users': WaterUser.objects.filter(is_active=True).count(),
            'total_bills': WaterBill.objects.count(),
            'pending_amount': float(WaterBill.objects.filter(status='pending').aggregate(total=Sum('total_fee'))['total'] or 0),
            'overdue_count': WaterBill.objects.filter(status='overdue').count(),
            'total_revenue': float(paid_fee),
            'usage_rate': round(float(paid_fee) / float(total_fee) * 100, 2) if total_fee > 0 else 0,
        })


class WaterPaymentViewSet(viewsets.ModelViewSet):
    queryset = WaterPayment.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bill', 'payment_method']
    search_fields = ['code', 'transaction_id']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterPaymentSerializer

    def perform_create(self, serializer):
        payment = serializer.save(
            code=generate_code('PAY'),
            operator=self.request.user,
        )
        bill = payment.bill
        bill.paid_fee = (bill.paid_fee or 0) + payment.amount

        if bill.paid_fee >= bill.total_fee:
            bill.status = 'paid'
        elif bill.paid_fee > 0:
            bill.status = 'partial'
        bill.save(update_fields=['paid_fee', 'status'])
