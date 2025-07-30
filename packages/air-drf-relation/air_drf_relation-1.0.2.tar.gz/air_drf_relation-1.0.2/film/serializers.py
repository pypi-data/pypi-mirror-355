from air_drf_relation.fields import AirRelatedField
from air_drf_relation.serializers import AirDataclassSerializer, AirModelSerializer

from .models import Actor, Film, FilmInformation


class ActorSerializer(AirModelSerializer):
    class Meta:
        model = Actor
        fields = ('id', 'name')


class FilmInformationSerializer(AirDataclassSerializer):
    class Meta:
        dataclass = FilmInformation


class FilmSerializer(AirModelSerializer):
    actors = AirRelatedField(ActorSerializer, many=True, as_serializer=True)
    information = FilmInformationSerializer()

    class Meta:
        model = Film
        fields = ('id', 'name', 'actors', 'information', 'release_date')

    def update_or_create(self, instance, validated_data):
        validated_data.pop('actors', None)
        return super().update_or_create(instance, validated_data)
