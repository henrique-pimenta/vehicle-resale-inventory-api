import json

import boto3
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.apps.vehicle.models import Vehicle, VehicleStatus
from inventory.apps.vehicle.serializers import VehicleSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_sold_param = self.request.query_params.get('is_sold', False)
        if self.action == 'list':
            return queryset.filter(is_sold=is_sold_param)
        return queryset

    @action(detail=False, methods=['post'], url_path='select-vehicle')
    def select_vehicle(self, request):
        vehicle_id = request.data.get('vehicle_id')

        if not vehicle_id:
            return Response({'error': 'vehicle_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            if vehicle.status in (VehicleStatus.SELECTED.value, VehicleStatus.SOLD.value):
                return Response(status=status.HTTP_404_NOT_FOUND)

            vehicle.status = VehicleStatus.SELECTED.value
            vehicle.save()

            detail = dict(VehicleSerializer(vehicle).data)
            detail['user_id'] = request.user
            self.publish_event('vehicle_selected', detail)

            return Response(status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='confirm-withdrawal', permission_classes=[IsAdminUser])
    def confirm_withdrawal(self, request):
        vehicle_id = request.data.get('vehicle_id')

        if vehicle_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        vehicle = Vehicle.objects.filter(vehicle_id=vehicle_id, status=VehicleStatus.SELECTED.value)
        if not vehicle.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        vehicle = vehicle.first()
        vehicle.status = VehicleStatus.SOLD.value
        vehicle.save()

        self.publish_event('withdrawal_confirmed', dict(VehicleSerializer(vehicle).data))

        return Response(status=status.HTTP_200_OK)

    def publish_event(self, event_type: str, detail: dict):
        event_bridge = boto3.client('events')
        event_bridge.put_events(
            Entries=[
                {
                    'Source': 'inventory_service',
                    'DetailType': event_type,
                    'Detail': json.dumps(detail),
                    'EventBusName': 'vehicle_resale_event_bus'
                }
            ]
        )

    @action(detail=False, methods=['post'], url_path='event-handler')
    def event_handler(self, request):
        if request.method == 'POST':
            event_data = request.data

            event_type = event_data.get("detail-type")
            if not event_type:
                return Response({'error': 'detail-type is required'}, status=status.HTTP_400_BAD_REQUEST)

            event_detail = event_data.get("detail")
            if not event_detail or not (vehicle_id := event_detail.get("vehicle_id")):
                return Response({'error': 'detail with vehicle_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)

                if event_type not in {'reservation_failed', 'payment_failed'}:
                    return Response({'error': 'unsupported event type'}, status=status.HTTP_400_BAD_REQUEST)

                vehicle.status = VehicleStatus.AVAILABLE.value
                vehicle.save()

                return Response(status=status.HTTP_200_OK)
            except:
                vehicle.status = VehicleStatus.AVAILABLE.value
                vehicle.save()
                self.publish_event('inventory_update_failed', event_detail)
                return Response(status=status.HTTP_400_BAD_REQUEST)
